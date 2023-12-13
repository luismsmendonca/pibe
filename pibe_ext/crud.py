import math
import logging
import datetime
import decimal
import types
import funcy as fn

import json
import peewee as pw

from webob import Response, exc
from playhouse.shortcuts import model_to_dict, dict_to_model

from .http import *
from .db import *

from functools import reduce
import operator

is_str = fn.isa(str)

__all__ = (
    "model_serializer",
    "get_object_or_404",
    "get_object_or_400",
    "get_object_or_422",
    "paginated",
    "filtered",
    "ordered",
    "skimmed",
    "object_list",
    "object_detail",
)

def model_serializer(
    model_class, fields=None, follow_m2m=True, exclude=None, extra=None, **serializers
):
    fields = fields or model_class._meta.fields.keys()
    if extra:
        fields = fields | extra

    if follow_m2m:
        fields = fields | model_class._meta.manytomany.keys()

    if exclude:
        fields = fields - set(exclude)

    def get_field_value(obj, field_name):
        if field_name in model_class._meta.fields:
            field = model_class._meta.fields[field_name]
        elif field_name in model_class._meta.manytomany:
            field = model_class._meta.manytomany[field_name]
        else:
            field = None

        if field and getattr(obj, field_name) is not None:
            if field.__class__ in (pw.DateField, pw.DateTimeField):
                return getattr(obj, field_name).isoformat()
            elif field.__class__ == pw.ForeignKeyField:
                return model_serializer(field.rel_model, follow_m2m=False)(
                    getattr(obj, field_name)
                )
            elif field.__class__ == pw.ManyToManyField:
                return model_serializer(field.rel_model, follow_m2m=False)(
                    getattr(obj, field_name)
                )
            elif field.__class__ == pw.DecimalField:
                return str(getattr(obj, field_name))

        return getattr(obj, field_name)

    defaults = dict(
        fn.lmap(
            lambda field_name: (
                field_name,
                lambda obj: get_field_value(obj, field_name),
            ),
            fields,
        )
    )
    serializers = fn.merge(defaults, serializers)

    def object_serializer(obj, project=None, omit=None):
        fields = serializers.keys()
        if project:
            fields = fields & project
        if omit:
            fields = fields - omit
        return dict([(f, serializers[f](obj)) for f in fields])

    def inner(qs, project=None, omit=None, **_fields):
        if isinstance(qs, pw.Model):
            return object_serializer(qs, project=project, omit=omit)
        return [object_serializer(obj, project=project, omit=omit) for obj in qs]

    return inner


def get_object_or_404(model_class, **kwargs):
    obj = model_class.get_or_none(**kwargs)
    if not obj:
        not_found(error="{} Not found".format(model_class.__name__))
    return obj


def get_object_or_400(model_class, **kwargs):
    obj = model_class.get_or_none(**kwargs)
    if not obj:
        bad_request(error="{} Not found".format(model_class.__name__))
    return obj


def get_object_or_422(model_class, **kwargs):
    obj = model_class.get_or_none(**kwargs)
    if not obj:
        unprocessable_entity(error="{} Not found".format(model_class.__name__))
    return obj


def paginated(req, qs, paginate_by=15, max_paginate_by=100):
    page = int(req.params.get("page", 1))
    paginate_by = min(int(req.params.get("paginate_by", paginate_by)), max_paginate_by)
    record_count = qs.count()
    page_count = int(math.ceil(record_count / paginate_by))
    return (
        qs.paginate(page, paginate_by),
        {
            "is_paginated": record_count > paginate_by,
            "page": page,
            "page_count": page_count,
            "record_count": record_count,
        },
    )


VALUE_CONVERSION = {"true": True, "false": False, "none": None}



@fn.memoize
def get_model_fields(model_class):
    return [f for f in model_class._meta.fields.keys()]


def filtered(req, qs, allowed_fields=None, omit_fields=None, expr_fns=None, **fns):

    params = req.params.mixed()

    filters = dict(
        fn.lmap(
            lambda x: (fn.cut_prefix(x[0], "filter__"), x[1]),
            fn.filter(lambda x: x[0].startswith("filter__"), fn.iteritems(params)),
        )
    )

    if filters:
        model_class = qs.model
        model_fields = get_model_fields(model_class)

        if allowed_fields:
            model_fields = [f for f in model_fields if f in allowed_fields]

        if omit_fields:
            model_fields = [f for f in model_fields if f not in omit_fields]

        expr_fns = expr_fns or {}

        _expr_list = []

        for fkey, value in filters.items():
            tokens = fkey.split("__")

            if len(tokens) == 1:
                field = tokens[0]
                op = "eq"
            elif len(tokens) == 2:
                field = tokens[0]
                op = tokens[1]

            # coerce values
            if op in ["in", "not_in"]:
                value = value if fn.is_list(value) else [value]
            elif is_str(value):
                value = VALUE_CONVERSION.get(value, value)

            print(field, op, value)

            if field in fns:
                qs = fns[field](req, qs, value)
                continue

            if field in expr_fns:
                _expr_list.append(expr_fns[field](value))
                continue

            if field not in model_fields:
                bad_request(error=f"field {field} not filterable")

            if op == "eq":
                _expr_list.append(getattr(model_class, field) == value)
            elif op == "in":
                _expr_list.append(getattr(model_class, field).in_(value))
            elif op == "not_in":
                _expr_list.append(getattr(model_class, field).not_in(value))
            elif op == "is_null":
                # FIXME assert boolean
                _expr_list.append(getattr(model_class, field).is_null(value))
            elif op == "contains":
                _expr_list.append(getattr(model_class, field).contains(value))
            else:
                bad_request(error=f"field: {field} unknown operation: {op}")

        if _expr_list:
            qs = qs.where(reduce(operator.and_, _expr_list))


    return qs


def ordered(req, qs, **order_fns):
    for order in req.params.getall("order_by"):
        direction = "desc" if order[0] == "-" else "asc"
        field_name = order[1:] if order[0] in ("+", "-") else order

        if field_name in order_fns:
            qs = order_fns[field_name](req, qs, direction)
        else:
            field = getattr(qs.model, field_name)
            if direction == "desc":
                field = field.desc()
            qs = qs.order_by(field)
    return qs


def skimmed(req, qs, serializer):
    return serializer(
        qs,
        project=req.params.getall("field") or None,
        omit=req.params.getall("exclude") or None,
    )


def object_list(
    req,
    qs,
    serializer=None,
    key_name=None,
    filter_kwargs=None,
    order_fns=None,
    paginate_by=15,
    max_paginate_by=100,

):
    serializer = serializer or qs.model.serializer()
    qs = filtered(req, qs, **(filter_kwargs or {}))
    qs = ordered(req, qs, **(order_fns or {}))
    (qs, pagination) = paginated(
        req, qs, paginate_by=paginate_by, max_paginate_by=max_paginate_by
    )
    key_name = key_name or f"{qs.model.__name__.lower()}_list"
    return {key_name: skimmed(req, qs, serializer), "pagination": pagination}


def object_detail(req, obj, serializer=None, key_name=None):
    serializer = serializer or obj.__class__.serializer()
    key_name = key_name or obj.__class__.__name__.lower()
    return {key_name: skimmed(req, obj, serializer)}
