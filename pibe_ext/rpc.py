import logging
from .http import http, no_content

logger = logging.getLogger(__name__)

__all__ = ("rpc",)

# https://www.jsonrpc.org/specification

class RPCRegistry(dict):
    def register(self, method_name=None):
        def func_decorator(func):
            self[method_name or func.__name__] = func
            return func

        return func_decorator

    def dispatch(self, wh_name, *args, **kwargs):
        for callback_fn in self.get(wh_name, []):
            callback_fn(*args, **kwargs)


rpc = RPCRegistry()


@http.post("/rpc")
def process_rpc(req):
    payload = req.json
    rpc_method = payload['method']
    rpc_params = payload['params']
    rpc_id = payload['id']

    resp = {
        "jsonrpc": "2.0",
        "id": rpc_id
    }

    try:
        resp["result"] = rpc["method"](*rpc_params)
    except:
        resp["error"] = "An error ocurred"

    return resp
