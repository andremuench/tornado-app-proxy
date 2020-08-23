class ApplicationSpec:
    
    def __init__(self, spec_id, image, display_name=None, description=None, cont_port=None, 
                 groups=None, network=None, env_list=None, internal=False):
        self.spec_id = spec_id
        self.display_name = display_name
        self.description = description
        self.image = image
        self.cont_port = cont_port
        self.network = network or "bridge"
        self.internal = internal or False
        self.env_list = env_list or dict()
        self.groups = groups

    @property
    def public(self):
        return self.groups is None 

    def __repr__(self):
        return str(self.__dict__)


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

    
class User:
    
    def __init__(self, username, groups=None):
        self.username = username
        self.groups = groups or []

    def __repr__(self):
        return f"<User(username={self.username},groups={self.groups})>"
