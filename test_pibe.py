import pytest
from webtest import TestApp
from unittest.mock import MagicMock
import pibe
from webob import Request, Response

def test_methods():
    route = pibe.Router()

    head_mock = MagicMock(return_value=Response())
    route.head("/head/")(head_mock)

    get_mock = MagicMock(return_value=Response())
    route.get("/get/")(get_mock)

    post_mock = MagicMock(return_value=Response())
    route.post("/post/")(post_mock)

    put_mock = MagicMock(return_value=Response())
    route.put("/put/")(put_mock)

    patch_mock = MagicMock(return_value=Response())
    route.patch("/patch/")(patch_mock)

    delete_mock = MagicMock(return_value=Response())
    route.delete("/delete/")(delete_mock)

    call_mock = MagicMock(return_value=Response())

    route("/call/", ["GET", "POST"])(call_mock)
    app = TestApp(route.application)

    app.head("/head/")
    assert head_mock.called

    app.get("/get/")
    assert get_mock.called

    app.post("/post/")
    assert post_mock.called

    app.put("/put/")
    assert put_mock.called

    app.patch("/patch/")
    assert patch_mock.called

    app.delete("/delete/")
    assert delete_mock.called


    app.get("/call/")
    assert call_mock.called


def test_match_methods():
    route = pibe.Router()

    get_mock = MagicMock(return_value=Response())
    route.get("/foo/")(get_mock)

    post_mock = MagicMock(return_value=Response())
    route.post("/foo/")(post_mock)

    app = TestApp(route.application)

    resp = app.put("/foo/", expect_errors=True)
    assert resp.status_code == 405
    assert get_mock.called is False
    assert post_mock.called is False

    app.get("/foo/")
    assert get_mock.called
    assert post_mock.called is False

    # reset mock
    get_mock.reset_mock()

    app.post("/foo/")
    assert get_mock.called is False
    assert post_mock.called


def test_method_call():
    route = pibe.Router()

    @route.get("/")
    def foo(req):
        return Response("ok")

    app = TestApp(route.application)

    resp = app.get("/")

    assert resp.text == "ok"


def test_method_not_allowed():

    route = pibe.Router()

    resource_mock = MagicMock(return_value=Response())
    route.get("/")(resource_mock)

    app = TestApp(route.application)

    assert app.post("/", expect_errors=True).status_code == 405
    assert app.head("/", expect_errors=True).status_code == 405
    assert app.put("/", expect_errors=True).status_code == 405
    assert app.patch("/", expect_errors=True).status_code == 405
    assert app.delete("/", expect_errors=True).status_code == 405

    # check it was never called
    assert resource_mock.called is False

    # now check the actual resource
    assert app.get("/").status_code == 200
    assert resource_mock.called

def test_not_found():
    route = pibe.Router()

    resource_mock = MagicMock(return_value=Response())

    route.get("/")(resource_mock)

    app = TestApp(route.application)

    assert app.get("/non-existent/", expect_errors=True).status_code == 404


def test_invalid_converter():
    route = pibe.Router()
    with pytest.raises(KeyError):
        # there is no foo converter
        route.get("/foo/<id:foo>/")(MagicMock())

def test_int_converter():
    route = pibe.Router()

    resource_mock = MagicMock(return_value=Response())

    route.get("/foo/<id:int>/")(resource_mock)

    app = TestApp(route.application)
    assert app.get("/foo/nonint/", expect_errors=True).status_code == 404

    assert app.get("/foo/123/").status_code == 200
    assert resource_mock.called
    assert len(resource_mock.call_args) == 2
    assert "id" in resource_mock.call_args[1]
    assert resource_mock.call_args[1]["id"] == "123"

def test_float_converter():
    route = pibe.Router()

    resource_mock = MagicMock(return_value=Response())

    route.get("/foo/<value:float>/")(resource_mock)

    app = TestApp(route.application)
    assert app.get("/foo/nonfloat/", expect_errors=True).status_code == 404

    assert app.get("/foo/1.23/").status_code == 200
    assert resource_mock.called
    assert len(resource_mock.call_args) == 2
    assert "value" in resource_mock.call_args[1]
    assert resource_mock.call_args[1]["value"] == "1.23"


def test_email_converter():
    route = pibe.Router()

    resource_mock = MagicMock(return_value=Response())
    route.get("/foo/<email:email>/")(resource_mock)

    app = TestApp(route.application)
    assert app.get("/foo/nonemail/", expect_errors=True).status_code == 404

    assert app.get("/foo/foo@bar.com/").status_code == 200
    assert resource_mock.called
    assert len(resource_mock.call_args) == 2
    assert "email" in resource_mock.call_args[1]
    assert resource_mock.call_args[1]["email"] == "foo@bar.com"


def test_named_routes():
    route = pibe.Router()

    route.get("/foo/", name="foo")(MagicMock(return_value=Response()))
    assert route.reverse("foo") == "/foo/"

    route.get("/bar/<bar_id>/", name="bar")(MagicMock(return_value=Response()))
    assert route.reverse("bar", bar_id=1) == "/bar/1/"

    route.get("/baaz/<baaz_id>/fooz/<foozz_id>/", name="baaz")(MagicMock(return_value=Response()))
    assert route.reverse("baaz", baaz_id=11, foozz_id=22) == "/baaz/11/fooz/22/"

    route.get("/foo-bar/", name="foo-bar")(MagicMock(return_value=Response()))
    assert route.reverse("foo-bar") == "/foo-bar/"

    route.get("/fooz-baaz/<baaz_id>/dummy/", name="fooz-baaz")(MagicMock(return_value=Response()))
    assert route.reverse("fooz-baaz", baaz_id=1) == "/fooz-baaz/1/dummy/"