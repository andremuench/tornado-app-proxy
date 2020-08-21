from torndsession.sessionhandler import SessionBaseHandler
from model import User


class LoginHandler(SessionBaseHandler):
    def get(self):
        self.write('<html><body><form action="" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.session["user"] = User(self.get_argument("name"))
        redirect_url = self.get_query_argument("redirect_url", default="/")
        self.redirect(redirect_url)


class LogoutHandler():
    def get(self):
        self.session.pop("user")
        self.redirect("/")


class SimpleAuthBackend:
    
    def add_handler(self, handler):
        handler.append((r"/login", LoginHandler))
        handler.append((r"/logout", LogoutHandler))

    def get_settings(self):
        return dict()
