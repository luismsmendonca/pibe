import funcy as fn
from webob import exc
from json.decoder import JSONDecodeError
import cerberus
from pibe import DotDict


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
            data = dict(call.req.json)
        except JSONDecodeError:
            not_acceptable(error="Invalid JSON Request")

    elif data_source == "params":
        data = dict(call.req.params)
    else:
        raise KeyError("unknown data source")

    v = cerberus.Validator(schema, **kwargs)
    if not v.validate(data):
        _raise_exc(exception_class, errors=v.errors)

    call.req.data = DotDict(v.document)

    return call()
