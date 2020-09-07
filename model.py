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

DEFAULT_PORT = 3838

class Application:

    def __init__(self, spec_id, container_id=None, port=None, status=None, external=False, latest_ping=None):
        self.spec_id = spec_id
        self.status = status
        self.container_id = container_id
        self.port = port or DEFAULT_PORT
        self.external = external
        self.latest_ping = latest_ping 

    
    def to_dict(self):
        data = dict()
        data.update(self.__dict__)
        data["url"] = self.get_url()
        return data

    @classmethod
    def from_dict(cls, data):
        spec_id = data.pop("spec_id")
        data.pop("url")
        return Application(spec_id, **data)

    def get_url(self):
        if self.external:
            return f"http://localhost:{self.port}"
        else:
            return f"http://{self.container_id[:12]}:{self.port}"

    
class User:
    
    def __init__(self, username, groups=None):
        self.username = username
        self.groups = groups or []

    def __repr__(self):
        return f"<User(username={self.username},groups={self.groups})>"
