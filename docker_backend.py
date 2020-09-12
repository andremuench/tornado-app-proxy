import docker
from model import Application
import model
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from tornado.ioloop import IOLoop

class DockerBackend:

    start_port = 3840
    _executor = None
    
    def __init__(self):
        self.client = docker.from_env()
        self.next_port = self.start_port

    @property
    def executor(self):
        cls = self.__class__
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(1)
        return cls._executor

    def get_next_port(self):
        _port = self.next_port
        self.next_port += 1
        return _port

    async def start_application(self, spec, user):
        container, external_port = await IOLoop.current().run_in_executor(self.executor, partial(self._run_container, spec, user))
        app = Application(spec.spec_id, container_id=container.id)
        if not spec.internal:
            app.port = external_port
            app.external = True
        app.status = model.STATUS_STARTING
        return app

    async def stop_application(self, app):
        def _stop():
            cnt = self.client.containers.get(app.container_id)
            if not cnt:
                return 
            cnt.stop()
            cnt.remove()
        await IOLoop.current().run_in_executor(self.executor, _stop)

    def _run_container(self, spec, user):
        external_port = None
        cont_port = spec.cont_port or 3838
        if not spec.internal:
            external_port = self.get_next_port()
            _ports = {f"{cont_port}/tcp": external_port}
        else:
            _ports = dict()

        _user_env = {
            "APP_PROXY_USER": user.username, 
            "APP_PROXY_GROUPS": ",".join(user.groups)
        }
        _env = dict()
        _env.update(spec.env_list)
        _env.update(_user_env)

        container = self.client.containers.run(spec.image, 
            detach=True, 
            ports=_ports, 
            environment=_env,
            network=spec.network)
        return container, external_port

