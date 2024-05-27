import logging
from pibe_ext.validator import *
from pibe_ext.http import http, no_content

logger = logging.getLogger(__name__)

__all__ = ("rpc",
        "JSONRPCParseError", "JSONRPCInvalidRequest", "JSONRPCMethodNotFound",
        "JSONRPCInvalidParams", "JSONRPCInternalError", "JSONRPCServerError",
)

# https://www.jsonrpc.org/specification

class JSONRPCException(Exception):

    def __init__(self, message=None, data=None):
        self.message = message or "Error"
        self.data = data or {}

class JSONRPCParseError(JSONRPCException):
    code = -32700

class JSONRPCInvalidRequest(JSONRPCException):
    code = -32600

class JSONRPCMethodNotFound(JSONRPCException):
    code = -32601

class JSONRPCInvalidParams(JSONRPCException):
    code = -32602

class JSONRPCInternalError(JSONRPCException):
    code = -32603

class JSONRPCServerError(JSONRPCException):
    def __init__(self, code=-32000, **kw):
        if not (code >= -32099 and code <= -32000):
            raise ValueError(f"Server error Code {code} has to be between -32000 and -32099")
        self.code = code
        super().__init__(**kw)


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
        resp["error"] = {"code": -32601, "message": "Method not found", "data": {}}
        return resp

    args = rpc_params if type(rpc_params) == list else []
    kwargs = rpc_params if type(rpc_params) == dict else {}

    try:
        resp["result"] = rpc[rpc_method](*args, **kwargs)
    except JSONRPCException as exc:
        resp["error"] = {"code": exc.code, "message": exc.message, "data": exc.data}
    except:
        logger.exception(f"RPC Server Error while executing rpc method: {rpc_method}", exc_info=True)
        resp["error"] = {"code": -32603, "message": "Internal error", "data": {}}

    return resp
