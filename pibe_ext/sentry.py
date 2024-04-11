import logging
from .settings import settings
from .appconfig import appconfig
from .http import http
from .session import g

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware


@appconfig.settings()
def sentry_settings(**opts):
    return {
        "use_sentry": appconfig.env.bool("USE_SENTRY", False),
        "sentry_dsn": appconfig.env("SENTRY_DSN", None),
    }



@appconfig.initialize()
def initialize_sentry(**opts):
    if settings.use_sentry:
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
    if settings.use_sentry:
        return SentryWsgiMiddleware(application)
    return application


@http.before_request()
def sentry_middleware(req):
    if settings.use_sentry:
        sentry_sdk.set_tag("correlation_id", req.correlation_id)
