import logging
from .settings import settings
from .appconfig import appconfig
from .http import http
from .session import g

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
except ImportError:
    raise ImportError("sentry_sdk has to be installed to use the sentry extension")


@appconfig.settings()
def sentry_settings(**opts):
    return {
        "sentry_dsn": appconfig.env("SENTRY_DSN", None),
    }


@appconfig.initialize()
def initialize_sentry(**opts):
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                LoggingIntegration(
                    level=settings.log_level, event_level=settings.log_level
                )
            ],
        )
        if settings.get("sentry_tags"):
            for k, v in settings.sentry_tags.items():
                sentry_sdk.set_tag(k, v)


@appconfig.wsgi_middleware()
def sentry_wsgi_middleware(application, **opts):
    if settings.sentry_dsn:
        return SentryWsgiMiddleware(application)
    return application


@http.before_request()
def sentry_middleware(req):
    if settings.sentry_dsn:
        sentry_sdk.set_tag("correlation_id", req.correlation_id)
