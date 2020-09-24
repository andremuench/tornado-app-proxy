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
    def __init__(self, url, tries=10, wait_sec=10):
        self.url = url
        self.tries = tries
        self.wait_sec = wait_sec

    async def watch(self):
        i = 0
        client = CurlAsyncHTTPClient()
        while i < self.tries:
            try:
                resp = await client.fetch(self.url)
                # TODO check response - only 2xx valid (3xx?)
                return
            except Exception as e:
                print("Error during watching", e)
                print("Not ready yet")
                i += 1
                await gen.sleep(self.wait_sec) 
        raise NoSuccessfulPingError


class RedisApplicationStore:
    
    def __init__(self):
        self.client = redis.Redis(host="redis-app-store", port=6379, db=0)

    def _key(self, username, spec_id):
        return f"{username}+{spec_id}"

    def from_key(self, key):
        username, spec_id = key.split("+")
        return username, spec_id

    def get(self, username, spec_id):
        data = self.client.get(self._key(username, spec_id))
        if not data:
            return None
        app = Application.from_dict(json.loads(data))
        return app

    def get_by_key(self, key):
        data = self.client.get(key)
        if not data:
            return None
        app = Application.from_dict(json.loads(data))
        return app

    def add(self, username, spec_id, app):
        self.set(username, spec_id, app)
        data = self.client.get("#apps")
        if not data:
            app_list = set() 
        else:
            app_list = set(json.loads(data))
        app_list.add(self._key(username, spec_id))
        data = json.dumps(list(app_list))
        self.client.set("#apps", data)

    def set(self, username, spec_id, app):
        data = app.to_dict()
        data = json.dumps(data)
        self.client.set(f"{username}+{spec_id}", data)
        self.client.set(f"{username}+{spec_id}+url", app.get_url())

    def delete(self, username, spec_id):
        self.client.delete(f"{username}+{spec_id}")
        self.client.delete(f"{username}+{spec_id}+url")
        data = self.client.get("#apps")
        if not data:
            return
        app_list = json.loads(data)
        app_list.remove(self._key(username, spec_id))
        self.client.set("#apps", json.dumps(app_list))

    def list(self):
        data = self.client.get("#apps")
        if not data:
            return []
        return [self.from_key(key) for key in json.loads(data)]


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
        app = await self.docker_backend.start_application(spec, user)
        app.status = model.STATUS_STARTING
        self.app_store.add(user.username, spec_id, app)
        watcher = ApplicationWatcher(app.get_url())
        try:
            await watcher.watch()
        except NoSuccessfulPingError as e:
            await self.docker_backend.stop_application(app)
            raise e
        app.latest_ping = time.time()
        app.status = model.STATUS_STARTED
        self.app_store.set(user.username, spec_id, app)
        return app

    async def remove_application(self, user, spec_id):
        app = self.app_store.get(user.username, spec_id)
        try:
            await self.docker_backend.stop_application(app)
        except:
            pass
        self.app_store.delete(user.username, spec_id)

    def app_keys(self):
        return self.app_store.list()

    async def on_pong(self, user, spec_id):
        app = self.app_store.get(user.username, spec_id)
        app.latest_ping = time.time()
        self.app_store.set(user.username, spec_id, app)
        
        

