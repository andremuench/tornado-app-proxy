from torndsession.sessionhandler import SessionBaseHandler
from model import User
from tornado.web import HTTPError
from .core import BaseLogoutHandler


class LoginHandler(SessionBaseHandler):

    def initialize(self, auth_store):
        self.auth_store = auth_store

    def get(self):
        self.write('<html><body><form action="" method="post">'
                   'Name: <input type="text" name="name">'
                   'Password: <input type="password" name="password">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        uid = self.get_argument("name")
        passwd = self.get_argument("password")
        try:
            _user, _pwd = self.auth_store[uid]
        except KeyError:
            raise HTTPError(403)
        if passwd != _pwd:
            raise HTTPError(403)
        self.session["user"] = _user
        self.set_secure_cookie("user", _user.username)
        redirect_url = self.get_query_argument("redirect_url", default="/")
        self.redirect(redirect_url)


users = {
    "andre": (User("andre", ["business", "admin"]), "abc"),
    "peter": (User("peter", ["business", "admin"]), "abc")
}


class SimpleAuthBackend:
    
    def add_handler(self, handler):
        handler.append((r"/login", LoginHandler, dict(auth_store=users)))
        handler.append((r"/logout", BaseLogoutHandler))

    def get_settings(self):
        return dict()
