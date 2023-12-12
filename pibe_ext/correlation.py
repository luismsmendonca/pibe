import uuid
from .session import g
from .http import http

__all__ = ("get_correlation_id", )

def get_correlation_id(req):
    return (
        req.headers.get("X-Correlation-ID")
        or req.params.get("correlation_id")
        or str(uuid.uuid4())
    )

@http.middleware()
def correlation_middleware(req, **opts):
    correlation_id = get_correlation_id(req)
    req.environ["correlation_id"] = correlation_id
    g.correlation_id = correlation_id
