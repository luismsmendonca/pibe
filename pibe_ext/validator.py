import funcy as fn
from webob import exc
from json.decoder import JSONDecodeError
import cerberus

from .http import _raise_exc, not_acceptable

__all__ = ("validate", )


@fn.decorator
def validate(
    call,
    schema,
    data_source="json_body",
    exception_class=exc.HTTPBadRequest,
    **kwargs):

    if data_source == "json_body":
        try:
            data = call.req.json
        except JSONDecodeError:
            not_acceptable(error="Invalid JSON Request")

    elif data_source == "params":
        data = call.req.params
    else:
        raise KeyError("unknown data source")

    v = cerberus.Validator(schema, **kwargs)
    if not v.validate(data):
        _raise_exc(exception_class, errors=v.errors)

    call.req.data = v.document

    return call()
