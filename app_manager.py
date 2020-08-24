import model 
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado import gen
import time
import tornado.ioloop


class NoSuccessfulPingError(Exception):
    pass


class ApplicationSpecNotFound(Exception):
    pass


class ApplicationWatcher:
    def __init__(self, url):
        self.url = url

    async def watch(self):
        i = 0
        client = CurlAsyncHTTPClient()
        while i < 10:
            try:
                resp = await client.fetch(f"http://{self.url}")
                return
            except Exception as e:
                print("Error during watching", e)
                print("Not ready yet")
                i += 1
                await gen.sleep(10) 
        raise NoSuccessfulPingError


class ApplicationManager:

    def __init__(self, spec_provider, docker_backend):
        self.data = dict()
        self.spec_provider = spec_provider
        self.docker_backend = docker_backend
   
    def get_application(self, user, spec_id):
        return self.data.get((user.username, spec_id))

    async def start_application(self, user, spec_id):
        spec = self.spec_provider.get(spec_id)
        if not spec:
            raise ApplicationSpecNotFound
        app = self.docker_backend.start_application(spec, user)
        app.user = user
        app.status = model.STATUS_STARTING
        self.register_app(user, app)
        watcher = ApplicationWatcher(app.get_url())
        await watcher.watch()
        app.latest_ping = time.time()
        async def check_ping():
            while True:
                now = time.time()
                if int(now - app.latest_ping) > 30:
                    print("No ping received since 30 sec - stopping")
                    self.remove_application(app)
                    break
                await gen.sleep(60)
        tornado.ioloop.IOLoop.current().spawn_callback(check_ping)
        app.status = model.STATUS_STARTED
        return app

    def register_app(self, user, app):
        self.data[(user.username, app.spec.spec_id)] = app

    def remove_application(self, app):
        self.docker_backend.stop_application(app)
        app.websocket.close(code=1001)
        self.data.pop((app.user.username, app.spec.spec_id))
        

