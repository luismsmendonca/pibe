import re
from functools import wraps
from webob import Request, Response, exc
from webob.dec import wsgify

__all__ = ("Router",)


var_regex = re.compile(
    r"""
    \<          # The exact character "<"
    (\w+)       # The variable name (restricted to a-z, 0-9, _)
    (?::(\w+)(\((.*)\))?)? # The optional part
    \>          # The exact character ">"
    """,
    re.VERBOSE,
)

parse_args = lambda args: map(lambda x: x.strip(), args.split(","))
parse_kwargs = lambda args, **defaults: dict(
    defaults,
    **dict(map(lambda x: x.split("="), map(lambda x: x.strip(), args.split(","))))
)


def int_converter(**kwargs):
    signed = kwargs.get("signed") in ["true", "1"]
    length = kwargs.get("length")
    signed_str = "[-+]?" if signed else ""
    length_str = "{{{}}}".format(length) if length else "+"
    return f"{signed_str}\d{length_str}"


def float_converter(**kwargs):
    signed = kwargs.get("signed") in ["true", "1"]
    signed_str = "[-+]?" if signed else ""
    return f"{signed_str}[0-9]*\.?[0-9]+"


regex_fn = {
    "default": "[^/]+",
    "str": "\w+",
    "year": "\d{4}",
    "month": "\d|1[0-2]",
    "day": "[0-2]\d|3[01]",
    "slug": "[\w-]+",
    "username": "[\w.@+-]+",
    "email": "(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}",
    "path": "[^/].*?",
    "uuid": "[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-"
            "[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    "int": int_converter,
    "float": float_converter,
    "any": lambda *a: "|".join(a),
    "re": lambda regexp: regexp,
}


def template_to_regex(template):
    regex = ""
    last_pos = 0
    for match in var_regex.finditer(template):
        regex += re.escape(template[last_pos : match.start()])
        var_name = match.group(1)
        kind = match.group(2) or "default"
        a_kw = match.group(4)
        args = [x.strip() for x in a_kw.split(",") if len(x.split("="))==1] if a_kw else ()
        kwargs = dict([[x.strip() for x in x.split("=")] for x in a_kw.split(",") if len(x.split("="))==2]) if a_kw else {}
        if kind not in regex_fn:
            raise KeyError("Unknown kind {}".format(kind))
        expr = "(?P<%s>%s)" % (
            var_name,
            regex_fn[kind](*args, **kwargs) if callable(regex_fn[kind]) else regex_fn[kind])
        regex += expr
        last_pos = match.end()
    regex += re.escape(template[last_pos:])
    regex = "^%s$" % regex
    return regex


def template_to_string(template):
    string = ""
    last_pos = 0
    for match in var_regex.finditer(template):
        string += template[last_pos : match.start()]
        var_name = match.group(1)
        string += "{{{}}}".format(var_name)
        last_pos = match.end()
    string += template[last_pos:]
    return string


class Router(list):
    def __init__(self, middleware=None):
        self.names = dict()
        self.middleware = middleware or []
        super().__init__()

    def resolve(self, req):
        uri_matched = False
        for (regex, resource, methods, opts) in self:
            match = regex.match(req.path_info)
            if match:
                uri_matched = True
                if req.method in methods:
                    return (resource, match.groupdict(), opts)

        # we got a match in uri but not in method
        if uri_matched:
            raise exc.HTTPMethodNotAllowed
        raise exc.HTTPNotFound


    @wsgify
    def application(self, req):
        (func, kwargs, opts) = self.resolve(req)
        if opts:
            for key, value in opts.items():
                setattr(req, key, value)

        # build the middleware
        mw_fns = [mw(req) for mw in self.middleware]

        # call the first leg
        for mw in mw_fns:
            interrupt_resp = next(mw)
            if interrupt_resp:
                return interrupt_resp

        # call the function
        resp = func(req, **kwargs)

        # reverse the middleware
        mw_fns.reverse()

        # call the last leg of the middleware
        for mw in mw_fns:
            try:
                interrupt_resp = mw.send(resp)
            except StopIteration:
                interrupt_resp = None
            if interrupt_resp:
                return interrupt_resp

        # finally return response
        return resp

    def add(self, pattern, methods=["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], name=None, **opts):
        if name:
            self.names[name] = template_to_string(pattern)
        def func_decorator(func):
            self.append((re.compile(template_to_regex(pattern)), func, methods, opts))
            return func
        return func_decorator

    def head(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["HEAD"], name=name, **opts)

    def get(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["GET"], name=name, **opts)

    def post(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["POST"], name=name, **opts)

    def put(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["PUT"], name=name, **opts)

    def patch(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["PATCH"], name=name, **opts)

    def delete(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["DELETE"], name=name, **opts)

    def options(self, pattern, name=None, **opts):
        return self.add(pattern, methods=["OPTIONS"], name=name, **opts)

    def __call__(self, pattern, methods, name=None, **opts):
        return self.add(pattern, methods, name=name, **opts)

    def reverse(self, name, *args, **kwargs):
        return self.names.get(name, "#unknown").format(*args, **kwargs)
