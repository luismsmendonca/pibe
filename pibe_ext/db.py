import sys
import json
import logging
from functools import partial
import funcy as fn

from webob.dec import wsgify

try:
    import peewee as pw
    from playhouse.db_url import connect
    from playhouse.shortcuts import model_to_dict, dict_to_model
    from playhouse.signals import Model as SignalModel
except ImportError:
    raise ImportError("peewee has to be installed to use the db extension")


from .settings import settings
from .crud import model_serializer
# from .init import init
from .http import http



logger = logging.getLogger(__name__)

__all__ = (
    "database",
    "Model",
    "db_models",
    "get_model_class",
    "initialize_database",
    "synchronize_database",
    "database_middleware",
    "db_connect",
    "db_atomic",
)


database = pw.Proxy()


class Model(pw.Model):
    class Meta:
        database = database

    @classmethod
    def serializer(cls, *a, **kw):
        return model_serializer(cls, *a, **kw)

    @classmethod
    def get_or_none(cls, *a, **kw):
        try:
            return cls.get(*a, **kw)
        except cls.DoesNotExist:
            return None

    def refresh(self):
        """To be used in tests"""
        return type(self).get(self._pk_expr())

    def update_from_dict(self, data):
        for key in data:
            if key != "id":
                if getattr(self, key) != data[key]:
                    setattr(self, key, data[key])


@fn.memoize
def db_models():
    return Model.__subclasses__()


@fn.memoize
def get_model_class(class_name):
    for model_class in db_models():
        if class_name in [model_class.__name__, model_class.__name__.lower()]:
            return model_class
    raise ValueError("No model with class {}".format(class_name))


@http.initialize()
def initialize_database(**opts):
    """Initialization method for the database.

    db is a Proxy object for the peewee database. This way it needs to be
    initialized. If connection fails it will issue a system exit.

    """
    db_url = opts.get("db_url")
    db_obj = connect(db_url or settings.database_url)
    database.initialize(db_obj)

    database.connect()
    database.close()
    try:
        database.connect()
        database.close()
    except:
        logger.error("Error connecting to database", exc_info=True)
        sys.exit(1)

    return db_obj


@fn.decorator
def db_connect(call):
    database.connect(reuse_if_open=True)
    try:
        resp = call()
    finally:
        if not database.is_closed():
            database.close()
    return resp


@fn.decorator
def db_atomic(call):
    with database.atomic():
        resp = call()
    return resp


@db_connect
def synchronize_database(drop_tables=None):
    if drop_tables:
        database.drop_tables(drop_tables)
    database.create_tables(db_models(), safe=True)


@wsgify.middleware
def database_middleware(req, app):
    database.connect(reuse_if_open=True)
    try:
        resp = req.get_response(app)
    finally:
        if not database.is_closed():
            database.close()
    return resp


@http.wsgi_middleware()
def add_database_middleware(application, **opts):
    if opts.get("database_middleware", True) == True:
        application = database_middleware(application)
    return application
