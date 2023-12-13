import logging
from .settings import settings
from .http import http
from .session import g

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware


@http.initialize()
def init_sentry(**opts):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            LoggingIntegration(
                level=settings.log_level, event_level=settings.log_level
            )
        ],
    )
    sentry_sdk.set_tag("service", "core-service")


@http.wsgi_middleware()
def sentry_wsgi_middleware(application, **opts):
    return SentryWsgiMiddleware(application)



@http.middleware()
def sentry_middleware(req, **opts):
    sentry_sdk.set_tag("correlation_id", g.correlation_id)
