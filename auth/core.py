from torndsession.sessionhandler import SessionBaseHandler


class BaseLogoutHandler(SessionBaseHandler):
    def get(self):
        self.session.delete("user")
        self.clear_cookie("user")
        self.redirect("/")
