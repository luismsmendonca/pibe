from gevent.local import local
from .http import http

__all__ = ("g", )

g = local()


@http.before_request()
def gevent_local_session_middleware(req):
    # populates the session object with the incoming request
    g.request = req
