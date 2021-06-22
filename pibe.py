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


def int_converter(args):
    kwargs = parse_kwargs(args) if args else {}
    length_str = "{{{}}}".format(kwargs["length"]) if kwargs.get("length") else "+"
    signed_str = "[-+]?" if bool(kwargs.get("signed")) else ""
    return "{}\d{}".format(signed_str, length_str)


def float_converter(args):
    kwargs = parse_kwargs(args) if args else {}
    signed_str = "[-+]?" if kwargs.get("signed") in ["true", "1"] else ""
    return "{}[0-9]*\.?[0-9]+".format(signed_str)


regex_fn = {
    "default": lambda args: "[^/]+",
    "str": lambda args: "\w+",
    "int": int_converter,
    "float": float_converter,
    "year": lambda args: "\d{4}",
    "month": lambda args: "\d|1[0-2]",
    "day": lambda args: "[0-2]\d|3[01]",
    "slug": lambda args: "[\w-]+",
    "username": lambda args: "[\w.@+-]+",
    "any": lambda args: "[{}]".format(parse_args(args)),
    "email": lambda args: "(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}",
    "re": lambda args: args,
}


def template_to_regex(template):
    regex = ""
    last_pos = 0
    for match in var_regex.finditer(template):
        regex += re.escape(template[last_pos : match.start()])
        var_name = match.group(1)
        kind = match.group(2) or "default"
        args = match.group(4)
        if kind not in regex_fn:
            raise KeyError("Unknown kind {}".format(kind))
        expr = "(?P<%s>%s)" % (var_name, regex_fn[kind](args))
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
    def __init__(self, append_slash=True):
        self.append_slash = append_slash
        self.names = dict()
        super().__init__()

    @wsgify
    def application(self, req):
        uri_matched = False
        for (regex, resource, methods) in self:
            path_info = (
                "{}/".format(req.path_info)
                if (req.path_info[-1] != "/") and self.append_slash
                else req.path_info
            )
            match = regex.match(path_info)
            if match:
                uri_matched = True
                if req.method in methods:
                    return resource(req, **match.groupdict())

        # we got a match in uri but not in method
        if uri_matched:
            raise exc.HTTPMethodNotAllowed
        raise exc.HTTPNotFound

    def add(self, pattern, methods=["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE"], name=None):
        if name:
            self.names[name] = template_to_string(pattern)

        def func_decorator(func):
            self.append((re.compile(template_to_regex(pattern)), func, methods))
            return func
        return func_decorator

    def head(self, pattern, name=None):
        return self.add(pattern, methods=["HEAD"], name=name)

    def get(self, pattern, name=None):
        return self.add(pattern, methods=["GET"], name=name)

    def post(self, pattern, name=None):
        return self.add(pattern, methods=["POST"], name=name)

    def put(self, pattern, name=None):
        return self.add(pattern, methods=["PUT"], name=name)

    def patch(self, pattern, name=None):
        return self.add(pattern, methods=["PATCH"], name=name)

    def delete(self, pattern, name=None):
        return self.add(pattern, methods=["DELETE"], name=name)

    def __call__(self, pattern, methods, name=None):
        return self.add(pattern, methods, name=name)

    def reverse(self, name, *args, **kwargs):
        return self.names.get(name, "#unknown").format(*args, **kwargs)
