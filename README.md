# pibe

Pibe is a simple WebOb router.


## Requirements

* webob >= 1.8.7

## Installation

This package can be installed using pip:

```
pip install pibe
```

## Usage

Here's a quick teaser of what you can do with pibe:

```
import pibe
from webob import Response
from wsgiref.simple_server import make_server

route = pibe.Router()

@route.get("/")
def hello_world(req):
    return Response("Hello World")

make_server('', 8000, route.application).serve_forever()
```


The rule format is done with `<>`. Example:

```
@route.get("/foo/<foo_id:int>/")
def get_foo(req, foo_id):
  return Response("{}".format(foo_id))
```

You can call the `get`, `post`, `put`, `patch` and `delete` methods to decorate a function.

```
@route.delete("/foo/<foo_id:int>/")
def delete_foo(req, foo_id):
  # go on and delete the object
  return Response("{}".format(foo_id))
```

The application will call with the request in first argument and the variables in subsequent arguments.

```
@route.put("/foo/<foo_id:int>/<email:email>/")
def put_foo(req, foo_id, email):
  return Response("{}".format(foo_id))
```

It will raise a 405 method not allowed webob exception if there is a match but an invalid method is used. It will raise a 404 not found if there is no match.

If you want the resource to be called by multiple methods you can use:

```
@route("/foo/<foo_id:int>/", methods=["GET", "PUT", "POST"])
def put_foo(req, foo_id):
  return Response("{}".format(foo_id))
```

You can also use name routes:

```
@route("/foo/<foo_id:int>/", methods=["GET", "PUT", "POST"], name="foo")
def foo_endpoint(req, foo_id):
  return Response("{}".format(foo_id))
```

and then you can call the reverse method:

```
url=route.reverse("foo", foo_id=1)
```

this will yield `/foo/1/`

The available converters are:

  - `str` - Matches a string
  - `int` - Matches an integer. Optional `length` argument. i.e.: `/foo/<id:int(length=2)>/`
  - `float` - Matches a float
  - `year` - Matches a year (4 numbers)
  - `month` - Matches a month (2 numbers)
  - `day` - Matches a day (2 numbers)
  - `slug` - Matches a slug
  - `username` - Matches a username. slug or email
  - `any` - Matches *any* of the given strings. Example `/foo/<action:any(BUY,SELL,HODL)>/`
  - `email` - Matches an email
  - `re` - Pass on any given regexp.
  - `path` - matches a path (forward slashes and file).
  - `uuid` - matches a uuid string.


To instantiate the application use:

```
route = pibe.Router()
(...)
route.application
```

Middlewares are written as a generator (pytest style) or as regular function:

```
def my_middleware(req, **opts):
    // before calling endpoint
    yield
    // after calling endpoint
```

```
def my_middleware(req, **opts):
    // before calling endpoint
    resp = yield
    // do something with the response
    // yield or not
```

```
def my_middleware(req, **opts):
    // before calling endpoint
    req.environ["foo"] = "bar"

```

Middleware can be initialized when instantiating the router class


```
route = pibe.Router(middlewares=[my_middleware1, my_middleware2])
```

or can be set at later stage

```
route.middlewares = [my_middleware1, my_middleware2]
```

or with a decorator:

```
@route.middleware()
def my_middleware(req, **opts):
    // before calling endpoint
    req.environ["fooz"] = "baaz"
    yield
    
```

middleware call is done in a pyramid fashion. i.e.:

```
my_middleware1 > my_middleware2 > dispatch > my_middleware2 > my_middleware1
```

## License

Pibe is offered under the `MIT-license`.
