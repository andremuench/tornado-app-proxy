from tornado.ioloop import IOLoop
from app_manager import RedisApplicationStore, ApplicationManager
from model import ApplicationSpec, User
from spec import SpecProvider
from docker_backend import DockerBackend
from tornado import gen

loop = IOLoop.current()

async def test_app_manager(spec_id="smst-app-2"):
    store = RedisApplicationStore()
    user = User("testuser", None)
    spec_prov = SpecProvider()
    backend = DockerBackend()
    app_manager = ApplicationManager(store, spec_prov, backend)
    # Begin case
    print("Starting app", spec_id)
    app = await app_manager.start_application(user, spec_id)
    app_in_store = store.get(user.username, spec_id)
    print("Spawned app is", app)
    print("App in store is", app_in_store)
    print("App list looks like", store.list())
    await gen.sleep(5)
    print("Stopping and removing app now", spec_id)
    await app_manager.remove_application(user, spec_id)
    app_in_store = store.get(user.username, spec_id)
    print("App in store is", app_in_store)
    print("App list looks like", store.list())
    
loop.add_callback(test_app_manager)
loop.start()
