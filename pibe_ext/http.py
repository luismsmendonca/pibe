import logging
import datetime
import decimal
import types
import funcy as fn
import json
from webob import Response, exc

import pibe
from pibe import JSONRouter

from .settings import settings

logger = logging.getLogger(__name__)

__all__ = (
    "http",
    "bad_request",
    "unauthorized",
    "forbidden",
    "not_found",
    "not_acceptable",
    "unprocessable_entity",
    "expectation_failed",
    "is_json",
    "no_content",
    "created",
)

class ExtRouter(JSONRouter):
    initialize_fns = []
    wsgi_middleware_fns = []

    def initialize(self):
        def func_decorator(func):
            self.initialize_fns.append(func)
            return func
        return func_decorator

    def wsgi_middleware(self):
        def func_decorator(func):
            self.wsgi_middleware_fns.append(func)
            return func
        return func_decorator

    def make_app(self, **opts):
        if opts.get("initialize", True) == True:
            settings.initialize(**opts)

            for init_func in self.initialize_fns:
                init_func(**opts)

        _app = self.application

        if opts.get("install_middleware", True) == True:
            for mw_fn in self.wsgi_middleware_fns:
                _app = mw_fn(_app, **opts)

        return _app

http = ExtRouter()
pibe.regex_fn["shortuuid"] = r"[2-9A-HJ-NP-Za-km-z]{22}"


def _raise_exc(
    exc_class,
    _default_error="Unknown Error Description",
    errors=None,
    error=None,
):
    raise exc_class(
        json= {"errors": errors or {"__all__": [error or _default_error]}},
        content_type="application/json",
    )


def bad_request(**kwargs):
    _raise_exc(exc.HTTPBadRequest, _default_error="Bad Request", **kwargs)


def unauthorized(**kwargs):
    _raise_exc(exc.HTTPUnauthorized, _default_error="Unauthorized", **kwargs)


def forbidden(**kwargs):
    _raise_exc(exc.HTTPForbidden, _default_error="Forbidden", **kwargs)


def not_found(**kwargs):
    _raise_exc(exc.HTTPNotFound, _default_error="Not Found", **kwargs)


def not_acceptable(**kwargs):
    _raise_exc(exc.HTTPNotAcceptable, _default_error="Not Acceptable", **kwargs)


def unprocessable_entity(**kwargs):
    _raise_exc(
        exc.HTTPUnprocessableEntity, _default_error="Unprocessable Entity", **kwargs
    )

def expectation_failed(**kwargs):
    _raise_exc(exc.HTTPExpectationFailed, _default_error="Expectation Failed", **kwargs)


@fn.decorator
def is_json(call):
    try:
        call.req.json
    except:
        not_acceptable(error="Invalid JSON request")
    return call()


@fn.decorator
def no_content(call):
    call()
    return Response(status=204)


@fn.decorator
def created(call):
    call()
    return Response(status=201)
