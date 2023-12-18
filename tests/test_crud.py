import peewee as pw
from webob import Request
from pibe_ext.crud import *
from pibe_ext.db import *

from playhouse.db_url import connect

def test_filtered():
    class Dummy(Model):
        name = pw.CharField()

    database.initialize(connect("sqlite:///:memory:"))
    database.create_tables([Dummy])

    d1 = Dummy.create(name="foo")
    d2 = Dummy.create(name="bar")

    qs = Dummy.select()

    req = Request(environ={
        'PATH_INFO': "/",
        'QUERY_STRING': "filter__name=dummy",
        'REQUEST_METHOD': 'GET',
    })

    result = filtered(req, qs)
    assert d1 not in result
    assert d2 not in result
