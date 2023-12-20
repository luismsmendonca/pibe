
import peewee as pw
import playhouse.postgres_ext as pw_pext

import funcy as fn
from webob import exc
from json.decoder import JSONDecodeError
import cerberus
from pibe import DotDict
import arrow

from .http import _raise_exc, not_acceptable

__all__ = (
    "model_schema",
    "model_validate"
)


FIELD_MAP = {
    'smallint': 'number',
    'bigint': 'number',
    'bool': 'boolean',
    'date': 'date',
    'datetime': 'datetime',
    'decimal': 'number',
    'double': 'number',
    'float': 'float',
    'int': 'integer',
    'time': 'string',
}

COERCE_MAP = {
    'float': float,
    'int': int,
    "date": lambda s: arrow.get(s).date(),
    "datetime": lambda s: arrow.get(s).datetime,
}

def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict)):  #noqa
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]

def model_schema(model_class, fields=None, exclude=None, schema=None):
    fields = fields or model_class._meta.fields.keys()
    exclude = exclude or []
    schema = schema or {}
    _schema = {}

    for name, field in model_class._meta.fields.items():
        if getattr(field, 'primary_key', False):
            continue
        if name in exclude:
            continue
        if fields and name not in fields:
            continue
        field_type = field.field_type.lower()
        required = not bool(getattr(field, 'null', True))
        if type(field) == pw_pext.ArrayField:
            ctype = "list"
        elif type(field) == pw_pext.HStoreField:
            ctype = "dict"
        else:
            ctype = FIELD_MAP.get(field_type, "string")

        field_schema = {
            "type": ctype,
            "required": True,
        }
        # field_schema["empty"] = not required
        choices = getattr(field, 'choices', ())
        if choices:
            field_schema["allowed"] = [c[0] for c in choices]
        default = getattr(field, 'default', None)
        max_length = getattr(field, 'max_length', None)
        if max_length:
            field_schema["maxlength"] = max_length

        unique = getattr(field, 'unique', False)
        coerce = COERCE_MAP.get(field_type)
        if coerce:
            field_schema["coerce"] = coerce
        _schema[name] = field_schema
    dict_merge(_schema, schema)
    return _schema


def model_validate(model_class,
    exception_class=exc.HTTPBadRequest,
    fields=None,
    exclude=None,
    schema=None,
    **kwargs):

    _schema = model_schema(model_class, fields=fields, exclude=exclude, schema=schema)

    def _deco(func):
        @fn.wraps(func)
        def wrapper(req, *args, **kwargs):
            try:
                data = dict(req.json)
            except JSONDecodeError:
                not_acceptable(error="Invalid JSON Request")

            v = cerberus.Validator(_schema, **kwargs)
            if not v.validate(data):
                _raise_exc(exception_class, errors=v.errors)

            req.data = DotDict(v.document)
            return func(req, *args, **kwargs)

        return wrapper
    return _deco
