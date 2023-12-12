from gevent.local import local
from .http import http

__all__ = ("g", )

g = local()


@http.middleware()
def gevent_local_session_middleware(req, **opts):
    # populates the session object with the incoming request
    g.request = req
