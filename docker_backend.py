import docker
from model import Application
import model

class DockerBackend:


    start_port = 3840
    
    def __init__(self):
        self.client = docker.from_env()
        self.next_port = self.start_port

    def get_next_port(self):
        _port = self.next_port
        self.next_port += 1
        return _port

    def start_application(self, spec):
        cont_port = spec.cont_port or 3838
        if not spec.internal:
            external_port = self.get_next_port()
            _ports = {f"{cont_port}/tcp": external_port}
        else:
            _ports = dict()

        container = self.client.containers.run(spec.image, detach=True, ports=_ports)
        app = Application(spec, container_id=container.id)
        if not spec.internal:
            app.port = external_port
            app.external = True
        app.status = model.STATUS_STARTING
        return app

    def stop_application(self, app):
        cnt = self.client.containers.get(app.container_id)
        # TODO Exception Handling
        if not cnt:
            pass
        cnt.stop()
        cnt.remove()

