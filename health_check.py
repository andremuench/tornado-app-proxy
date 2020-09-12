import time
from model import User, STATUS_STARTED

class HealthCheck:
    
    def __init__(self, app_manager):
        self.app_manager = app_manager

    async def run_check(self):
        app_key_list = self.app_manager.app_keys()
        for username, spec_id in app_key_list:
            user = User(username, None)
            _app = self.app_manager.get_application(user, spec_id)
            if not _app:
                continue
            if _app.status != STATUS_STARTED:
                print("Status is", _app.status)
                continue
            now = time.time()
            if int(now - _app.latest_ping) > 30:
                print("No ping received since 30 sec - stopping")
                await self.app_manager.remove_application(user, spec_id)

