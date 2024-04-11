import logging
from pibe_ext.validator import *
from pibe_ext.http import http, no_content

logger = logging.getLogger(__name__)

__all__ = ("rpc",)

# https://www.jsonrpc.org/specification

class RPCRegistry(dict):
    def __call__(self, method_name=None):
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
    try:
        payload = req.json
    except:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"}
        }

    rpc_method = payload.get("method")
    rpc_params = payload.get("params")
    rpc_id =  payload.get("id")

    resp = {
        "jsonrpc": "2.0",
        "id": rpc_id
    }

    func = rpc.get(rpc_method)
    if not func:
        resp["error"] = {"code": -32601, "message": "Method not found"}
        return resp

    args = rpc_params if type(rpc_params) == list else []
    kwargs = rpc_params if type(rpc_params) == dict else {}

    try:
        resp["result"] = rpc[rpc_method](*args, **kwargs)
    except:
        logger.exception(f"RPC Server Error while executing rpc method: {rpc_method}", exc_info=True)
        resp["error"] = {"code": -32000, "message": "Server Error"}

    return resp
