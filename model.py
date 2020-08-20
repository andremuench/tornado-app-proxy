class ApplicationSpec:
    
    def __init__(self, spec_id, display_name, description, image, cont_port, network=None, internal=False):
        self.spec_id = spec_id
        self.display_name = display_name
        self.description = description
        self.image = image
        self.cont_port = cont_port
        self.network = network
        self.internal = internal


STATUS_STARTING = "starting"
STATUS_STARTED = "started"

class Application:
    
    def __init__(self, spec, container_id=None, port=None, external=False):
        self.spec = spec
        self.status = None
        self.container_id = container_id
        self.port = port
        self.external = external


    def get_url(self):
        if self.external:
            return f"localhost:{self.port}"
        else:
            return f"{self.container_id}:{self.port}"

    

