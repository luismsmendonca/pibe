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
    "bad_gateway",
    "is_json",
    "no_content",
    "created",
)


http = JSONRouter()
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


def bad_gateway(**kwargs):
    _raise_exc(exc.HTTPBadGateway, _default_error="Bad Gateway", **kwargs)



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
