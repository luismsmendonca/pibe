from pibe_ext.appconfig import *
from werkzeug.debug import DebuggedApplication

__all__ = ()

@appconfig.wsgi_middleware()
def install_debugger_middleware(application, **opts):
    if opts.get("use_debugger", False) == True:
        application = DebuggedApplication(application, evalex=True)
    return application
