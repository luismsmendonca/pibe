import funcy as fn
import requests

__all__ = ("ApiWrapper", "api_headers",)


class HeaderRegistry(list):
    def __call__(self):
        def func_decorator(func):
            self.append(func)
            return func
        return func_decorator

api_headers = HeaderRegistry()

class ApiWrapper(object):
    host = None
    methods = ["get", "post", "put", "delete", "head", "patch", "options"]

    def __init__(self):
        for method in self.methods:
            setattr(self, method, fn.partial(self.call, method))

    def get_headers(self):
        headers = {}
        for api_header_fn in api_headers:
            api_header_fn(headers)
        return headers

    def call(self, method, uri, *args, **kwargs):
        if not self.host:
            raise RuntimeError("Host not defined")

        kwargs["headers"] = fn.merge(kwargs.get("headers", {}), self.get_headers())
        return getattr(requests, method)(f"{self.host}{uri}", *args, **kwargs)
