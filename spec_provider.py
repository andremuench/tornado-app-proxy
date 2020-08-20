from model import ApplicationSpec

class SpecProvider:
    def __init__(self):
        self.data = dict()
        self.load()

    def load(self):
        self.data["smst-app"] = ApplicationSpec("smst-app", "SMST Application", "Custom development", "smst_app:1.1b0", 3838)
        self.data["smst-app-2"] = ApplicationSpec("smst-app-2", "SMST Application 2", "Custom development", "smst_app:1.1b0", 3838)

    def get(self, spec_id):
        return self.data.get(spec_id)
