import funcy as fn
import peewee as pw


__all__ = (
    "model_serializer",
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
