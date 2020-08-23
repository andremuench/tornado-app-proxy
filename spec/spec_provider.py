from model import ApplicationSpec
from marshmallow import Schema, fields, post_load


class ContainerSchema(Schema):
    image = fields.Str(required=True)
    internal = fields.Bool()
    port = fields.Int()
    network = fields.Str()
    env = fields.Dict()


class SpecSchema(Schema):
    spec_id = fields.Str(required=True)
    display_name = fields.Str()
    description = fields.Str()
    container = fields.Nested(ContainerSchema)
    groups = fields.List(fields.Str())

    @post_load
    def objectify(self, data, **kwargs):
        return ApplicationSpec(
            data["spec_id"], 
            data["container"]["image"],
            display_name=data.get("display_name"), 
            description=data.get("description"), 
            cont_port=data["container"].get("port"),
            groups=data.get("groups"),
            internal=data.get("internal"),
            env_list=data["container"].get("env")
            )
        

class SpecProvider:
    def __init__(self):
        self.data = dict()
        self.load()

    def load(self):
        try:
            from spec.setting import specs as _specs
            _specs = SpecSchema().load(_specs, many=True)
            print(_specs)
            for s in _specs:
                self.data[s.spec_id] = s
        except ImportError as e:
            print(e)

    def get(self, spec_id):
        return self.data.get(spec_id)

    def list(self, groups):
        def _gen():
            for spec in self.data.values():
                if spec.public:
                    yield spec
                elif set(spec.groups or []).insection(set(groups)):
                    yield spec
        return list(_gen())
