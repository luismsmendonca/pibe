import logging
from .settings import settings
from .http import http
from .session import g

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware


@http.initialize()
def init_sentry(**opts):
    if opts.get("use_sentry", True):
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


@http.wsgi_middleware()
def sentry_wsgi_middleware(application, **opts):
    if opts.get("use_sentry", True):
        return SentryWsgiMiddleware(application)
    return application


@http.middleware()
def sentry_middleware(req, **opts):
    if opts.get("use_sentry", True):
        sentry_sdk.set_tag("correlation_id", g.correlation_id)
