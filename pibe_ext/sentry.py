import logging
from app.core import settings, http, g

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware


@http.initialize()
def init_sentry(**opts):
    if settings.use_sentry:
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
def install_sentry_middleware(application, **opts):
    if settings.use_sentry:
        application = SentryWsgiMiddleware(application)
    return application


@http.middleware()
def add_correlation_id(req, **opts):
    if settings.use_sentry:
        sentry_sdk.set_tag("correlation_id", g.correlation_id)
