from torndsession.sessionhandler import SessionBaseHandler


class BaseLogoutHandler(SessionBaseHandler):
    def get(self):
        self.session.pop("user")
        self.redirect("/")
