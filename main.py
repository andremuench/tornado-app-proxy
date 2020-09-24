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
from app_manager import ApplicationManager, ApplicationSpecNotFound, SessionApplicationStore, RedisApplicationStore
from auth import get_auth_backend
from torndsession.sessionhandler import SessionBaseHandler
from tornado.web import StaticFileHandler
import os
from health_check import HealthCheck


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
        

class ApplicationPingHandler(BaseHandler):
    
    def initialize(self, app_manager):
        self.app_manager = app_manager

    async def post(self, path):
        user = self.current_user
        await self.app_manager.on_pong(user, path)


docker_backend = DockerBackend()
spec_provider = SpecProvider()
app_manager = ApplicationManager(RedisApplicationStore(), spec_provider, docker_backend)
health_check = HealthCheck(app_manager)



class Application(tornado.web.Application):
    def __init__(self, handlers, **settings):
        session_settings = dict(
            driver="redis",
            driver_settings=dict(
                host='172.22.0.4',
                port=6379,
                db=0,
                max_connections=1024,
            )
        )
        settings.update(session=session_settings)
        tornado.web.Application.__init__(self, handlers=handlers, **settings)

settings = {
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__", 
    "websocket_ping_interval": 10,
    "autoreload": False,
    "debug": True,
    "static_path": os.path.join(os.path.dirname(__file__), "static")
}

handlers = [ 
    (r"/", MainHandler),
    (r"/app-list", ApplicationListHandler, dict(spec_provider=spec_provider)),
    (r"/app/([\w\-]+)", ApplicationHandler, dict(app_manager=app_manager)),
    (r"/app-ping/([\w\-]+)", ApplicationPingHandler, dict(app_manager=app_manager)),
    (r"/static/(.*)", StaticFileHandler, dict(path=settings["static_path"])),
]

auth_backend = get_auth_backend('simple')
auth_backend.add_handler(handlers)
settings.update(auth_backend.get_settings())
 
application = Application(handlers, **settings)


async def check_health():
    while True:
        await gen.sleep(30)
        await health_check.run_check()

if __name__ == '__main__':
    server = tornado.web.HTTPServer(application)
    server.bind(8888)
    server.start(1)
    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(check_health)
    ioloop.start()
