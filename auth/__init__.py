

def get_auth_backend(name):
    if name == 'simple':
        from .simple_auth import SimpleAuthBackend
        return SimpleAuthBackend()
    elif name == 'saml':
        from .saml import SamlBackend
        return SamlBackend()
