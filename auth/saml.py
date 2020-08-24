from tornado.web import RequestHandler
import tornado.httputil
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from model import User
from torndsession.sessionhandler import SessionBaseHandler


SAML_UID_ATTR = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"

class LoginHandler(SessionBaseHandler):
    def get(self):
        req = prepare_tornado_request(self.request)
        auth = init_saml_auth(req)
        self.redirect(auth.login())

    def post(self):
        req = prepare_tornado_request(self.request)
        auth = init_saml_auth(req)
        error_reason = None
        attributes = False
        paint_logout = False
        success_slo = False

        auth.process_response()
        errors = auth.get_errors()
        if errors:
            raise Exception(errors)
        self.session["user"] = User(auth.get_attributes()[SAML_UID_ATTR][0])
        self.session["samlNameId"] = auth.get_nameid()
        self.session["samlSessionIndex"] = auth.get_session_index()
        redirect_url = self.session.get("initial_request_url") or "/"
        self.redirect(redirect_url)


class LogoutHandler(SessionBaseHandler):
    def get(self):
        req = prepare_tornado_request(self.request)
        auth = init_saml_auth(req)
        if 'sls' in req['get_data']:
            _logout = lambda: self.session.delete("user")
            url = auth.process_slo(delete_session=_logout)
            errors = auth.get_errors()
            if url:
                self.redirect(url)
        else:
            name_id = self.session.get('samlNameId')
            session_index = self.session.get('samlSessionIndex')
            self.redirect(auth.logout(name_id=name_id, session_index=session_index))
        

class SamlBackend:

    def add_handler(self, handler):
        handler.append((r"/login", LoginHandler))
        handler.append((r"/logout", LogoutHandler))

    def get_settings(self):
        return dict(saml_path="saml")


def prepare_tornado_request(request):
    dataDict = {}
    for key in request.arguments:
        dataDict[key] = request.arguments[key][0].decode('utf-8')

    result = {
        'https': 'on' if request == 'https' else 'off',
        'http_host': tornado.httputil.split_host_and_port(request.host)[0],
        'script_name': request.path,
        'server_port': tornado.httputil.split_host_and_port(request.host)[1],
        'get_data': dataDict,
        'post_data': dataDict,
        'query_string': request.query
    }
    return result


def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path="saml")
    return auth
