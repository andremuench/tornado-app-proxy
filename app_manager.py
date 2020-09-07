import model 
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado import gen
import time
import tornado.ioloop
import redis
import json
from model import Application


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
                resp = await client.fetch(self.url)
                return
            except Exception as e:
                print("Error during watching", e)
                print("Not ready yet")
                i += 1
                await gen.sleep(10) 
        raise NoSuccessfulPingError


class RedisApplicationStore:
    
    def __init__(self):
        self.client = redis.Redis(host="86d568cdf434", port=6379, db=0)

    def get(self, username, spec_id):
        data = self.client.get(f"{username}+{spec_id}")
        if not data:
            return None
        app = Application.from_dict(json.loads(data))
        return app

    def set(self, username, spec_id, app):
        data = app.to_dict()
        data = json.dumps(data)
        self.client.set(f"{username}+{spec_id}", data)

    def delete(self, username, spec_id):
        self.client.delete(f"{username}+{spec_id}")


class SessionApplicationStore:

    SESSION_KEY = "apps"
    
    def __init__(self, session):
        self.session = session

    def get(self, username, spec_id):
        apps = self.session.get(self.SESSION_KEY)
        if apps:
            return apps.get(spec_id)
        return None

    def set(self, username, spec_id, app):
        apps = self.session.get(self.SESSION_KEY)
        if not apps:
            apps = dict()
        apps[spec_id] = app
        self.session[self.SESSION_KEY] = apps

    def delete(self, username, spec_id):
        apps = self.session.get(self.SESSION_KEY)
        if apps:
            apps.pop(spec_id)
            self.session[self.SESSION_KEY] = apps
            self.session.flush()


class ApplicationManager:

    def __init__(self, app_store, spec_provider, docker_backend):
        self.app_store = app_store
        self.spec_provider = spec_provider
        self.docker_backend = docker_backend
   
    def get_application(self, user, spec_id):
        return self.app_store.get(user.username, spec_id)

    async def start_application(self, user, spec_id):
        spec = self.spec_provider.get(spec_id)
        if not spec:
            raise ApplicationSpecNotFound
        app = self.docker_backend.start_application(spec, user)
        app.status = model.STATUS_STARTING
        self.app_store.set(user.username, spec_id, app)
        watcher = ApplicationWatcher(app.get_url())
        await watcher.watch()
        app.latest_ping = time.time()
        async def check_ping():
            while True:
                await gen.sleep(60)
                _app = self.app_store.get(user.username, spec_id)
                now = time.time()
                if int(now - _app.latest_ping) > 30:
                    print("No ping received since 30 sec - stopping")
                    self.remove_application(user, spec_id)
                    break
        tornado.ioloop.IOLoop.current().spawn_callback(check_ping)
        app.status = model.STATUS_STARTED
        self.app_store.set(user.username, spec_id, app)
        return app

    def remove_application(self, user, spec_id):
        app = self.app_store.get(user, spec_id)
        try:
            self.docker_backend.stop_application(app)
        except:
            pass
        self.app_store.delete(user.username, spec_id)

    def pong(self, user, spec_id):
        app = self.app_store.get(user.username, spec_id)
        app.latest_ping = time.time()
        self.app_store.set(user.username, spec_id, app)
        
        

