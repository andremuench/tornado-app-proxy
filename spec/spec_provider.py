from model import ApplicationSpec
from marshmallow import Schema, fields, post_load


class ContainerSchema(Schema):
    image = fields.Str()
    internal = fields.Bool()
    port = fields.Int()


class SpecSchema(Schema):
    spec_id = fields.Str()
    display_name = fields.Str()
    description = fields.Str()
    container = fields.Nested(ContainerSchema)

    @post_load
    def objectify(self, data, **kwargs):
        return ApplicationSpec(data["spec_id"], data["display_name"], data["description"], data["container"]["image"],
            data["container"]["port"])
        
    

class SpecProvider:
    def __init__(self):
        self.data = dict()
        self.load()

    def load(self):
        try:
            from spec.setting import specs as _specs
            _specs = SpecSchema().load(_specs, many=True)
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
