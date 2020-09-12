from tornado.ioloop import IOLoop
from app_manager import RedisApplicationStore, ApplicationManager
from model import ApplicationSpec, User
from spec import SpecProvider
from docker_backend import DockerBackend
from tornado import gen
from health_check import HealthCheck

loop = IOLoop.current()

store = RedisApplicationStore()
spec_prov = SpecProvider()
backend = DockerBackend()
app_manager = ApplicationManager(store, spec_prov, backend)
health_check = HealthCheck(app_manager)

async def test_app_manager(spec_id="smst-app-2"):
    user = User("testuser", None)
    # Begin case
    print("Starting app", spec_id)
    app = await app_manager.start_application(user, spec_id)
    app_in_store = store.get(user.username, spec_id)
    print("Spawned app is", app)
    print("App in store is", app_in_store)
    print("App list looks like", store.list())
    await gen.sleep(180)
    print("Stopping and removing app now", spec_id)
    await app_manager.remove_application(user, spec_id)
    app_in_store = store.get(user.username, spec_id)
    print("App in store is", app_in_store)
    print("App list looks like", store.list())

async def test_health():
    while True:
        print("Testing health")
        try:
            await health_check.run_check()
        except Exception as e:
            print("Error during health check", e)
        await gen.sleep(30)
    
loop.add_callback(test_app_manager)
loop.add_callback(test_health)
loop.start()
