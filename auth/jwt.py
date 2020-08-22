from .core import BaseLogoutHandler
from torndsession.sessionhandler import SessionBaseHandler
from authlib.jose import jwt
from tornado.web import HTTPError
from authlib.jose.errors import ExpiredTokenError, InvalidClaimError
from model import User


class LoginHandler(SessionBaseHandler):
    def initialize(self, pubkey, jwt_settings):
        self.pubkey = pubkey
        self.jwt_settings = jwt_settings

    def get(self):
        try:
            _auth_header = self.request.headers["Authorization"]
            _type, token = _auth_header.split()
        except (ValueError, KeyError):
            raise HTTPError(401)
        _iss = self.jwt_settings.get("iss")
        claims_options = {
            "iss": {
                "essential": True,
                "values": _iss
            }
        }
        claims = jwt.decode(token, self.pubkey, claims_options=claims_options)
        try:
            claims.validate()
        except (ExpiredTokenError, InvalidClaimError):
            raise HTTPError(401)
        _username_claim = self.jwt_settings.get("user_claim", "uid")
        _groups_claim = self.jwt_settings.get("group_claim", "groups")
        _username = claims.get(_username_claim)
        _groups = claims.get(_groups_claim)
        self.session["user"] = User(_username, _groups)
        self.redirect("/")

    
class JWTAuthBackend:
    
    def __init__(self):
        with open("jwt/public.pem") as f:
            self.key = f.read()
        try:
            from jwt.config import settings as _settings
            self.settings = _settings
        except Exception as e:
            print(e)
    
    def add_handler(self, handler):
        handler.append((r"/login", LoginHandler, dict(pubkey=self.key, jwt_settings=self.settings)))
        handler.append((r"/logout", BaseLogoutHandler))

    def get_settings(self):
        return dict()
