import tornado
from collections.abc import Callable
from model import User
import re
import tornado.web
import tornado.ioloop
from tornado.curl_httpclient import CurlAsyncHTTPClient, CurlError
from tornado.httpclient import HTTPClient
import tornado.websocket
from tornado.websocket import websocket_connect
import docker
import time
from docker_backend import DockerBackend
from spec import SpecProvider
from tornado import gen
from app_manager import ApplicationManager, ApplicationSpecNotFound
from auth import get_auth_backend
from torndsession.sessionhandler import SessionBaseHandler


class BaseHandler(SessionBaseHandler):

    def prepare(self):
        self.session["initial_request_url"] = self.request.uri
    
    def get_current_user(self):
        return self.session.get("user")


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login?redirect_url=/")
            return
        name = tornado.escape.xhtml_escape(self.current_user.username)
        self.write("Hello, " + name)


class HeaderCallback(Callable):

    def __init__(self):
        self.headers = dict()

    def __call__(self, line):
        try:
            k,v = line.strip().split(":")
            self.headers[k.strip()] = v.strip()
        except ValueError:
            pass
        

class ApplicationProxyHandler(BaseHandler):

    def initialize(self, app_manager):
        self.app_manager = app_manager

    async def get(self, app_id, path):
        if not self.current_user:
            raise tornado.web.HTTPError(401)
        app = self.app_manager.get_application(self.current_user, app_id)
        if not app:
            raise tornado.web.HTTPError(404)
        app_url = app.get_url()
        http_client = CurlAsyncHTTPClient()
        _headers = self.request.headers
        try:
            header_c = HeaderCallback()
            response = await http_client.fetch(f"http://{app_url}/{path}", raise_error=False,
            header_callback=header_c, headers=_headers)
        except CurlError:
            if header_c.headers.get("Upgrade", None) == "websocket":
                print("Upgrading in get")
                self.set_status(101)
                for k,v in header_c.headers.items():
                    self.set_header(k,v)
        except Exception as e:
            print(path, "Error: %s" % e)
        else:
            if response.code == 200:
                if response.headers["Content-Type"] == "text/html":
                    body = re.sub(r"(href|src)=(\")?/",f"\\1=\\2/app-proxy/{app_id}", response.body.decode()).encode()
                else:
                    body = response.body
                self.set_header("Content-Type", response.headers["Content-Type"])
                self.write(body)

    async def post(self, app_id, path):
        if not self.current_user:
            raise tornado.web.HTTPError(401)
        app = self.app_manager.get_application(self.current_user, app_id)
        if not app:
            raise tornado.web.HTTPError(404)
        app_url = app.get_url()

        http_client = CurlAsyncHTTPClient()
        _headers = self.request.headers
        try:
            header_c = HeaderCallback()
            response = await http_client.fetch(f"http://{app_url}/{path}", method="POST", raise_error=False,
                                               header_callback=header_c, headers=_headers,
                                               allow_nonstandard_methods=True, body=self.request.body)
        except Exception as e:
            print(path, "Error: %s" % e)
        else:
            self.set_header("Content-Type", response.headers["Content-Type"])
            self.set_status(response.code)
            self.write(response.body)


class WebSocketHandler(tornado.websocket.WebSocketHandler, BaseHandler):

    def initialize(self, app_manager):
        self.app_manager = app_manager
    
    async def open(self, app_id):
        self.app = self.app_manager.get_application(self.current_user, app_id)

        def call_write(msg):
            if msg:
                self.write_message(msg)

        self.websocket = await websocket_connect(f"ws://{self.app.get_url()}/websocket/", on_message_callback=call_write)
        self.app.websocket = self

    async def on_message(self, message):
        if self.websocket:
            self.websocket.write_message(message)

    def on_pong(self, data):
        self.app.latest_ping = time.time()

    def on_close(self):
        self.websocket.close(self.close_code, self.close_reason)


class ApplicationHandler(BaseHandler):

    def initialize(self, app_manager):
        self.app_manager = app_manager

    def get(self, app_id):
        if not self.current_user:
            self.redirect("/login")
            return
        self.render("app.html", title=app_id, applink=f"/app-proxy/{app_id}/")

    async def post(self, app_id):
        if not self.current_user:
            raise tornado.web.HTTPError(401)
        app = self.app_manager.get_application(self.current_user, app_id)
        if not app:
            try:
                app = await self.app_manager.start_application(self.current_user, app_id)
            except ApplicationSpecNotFound:
                raise tornado.web.HTTPError(404)
        self.write(dict(app_url=f"/app-proxy/{app_id}/"))


class ApplicationListHandler(BaseHandler):

    def initialize(self, spec_provider):
        self.spec_provider = spec_provider
    
    def get(self):
        user = self.current_user
        if not user:
            self.redirect("/login?redirect_url=/app-list")
            return
        apps = spec_provider.list(user.groups)
        self.render("app_list.html", appList=apps, title="App Proxy")
        

docker_backend = DockerBackend()
spec_provider = SpecProvider()
app_manager = ApplicationManager(spec_provider, docker_backend)
user_apps = dict()

class Application(tornado.web.Application):
    def __init__(self, handlers, **settings):
        session_settings = dict(
            driver="memory",
            driver_settings={'host': self},
            sid_name='torndsesionID',  # default is msid.
            session_lifetime=1800,  # default is 1200 seconds.
            force_persistence=True,
        )
        settings.update(session=session_settings)
        tornado.web.Application.__init__(self, handlers=handlers, **settings)

handlers = [ 
    (r"/", MainHandler),
    (r"/app-list", ApplicationListHandler, dict(spec_provider=spec_provider)),
    (r"/app-proxy/([\w\-]+)/websocket/", WebSocketHandler, dict(app_manager=app_manager)),
    (r"/app-proxy/([\w\-]+)/(.*)", ApplicationProxyHandler, dict(app_manager=app_manager)),
    (r"/app/([\w\-]+)", ApplicationHandler, dict(app_manager=app_manager)),
]

settings = {
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__", 
    "websocket_ping_interval": 10,
    "autoreload": False,
    "debug": True
}

auth_backend = get_auth_backend('simple')
auth_backend.add_handler(handlers)
settings.update(auth_backend.get_settings())
 
application = Application(handlers, **settings)


if __name__ == '__main__':
    server = tornado.web.HTTPServer(application)
    server.bind(8888)
    server.start(1)
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.start()
