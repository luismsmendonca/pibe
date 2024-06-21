import os
import logging
from environs import Env
import funcy as fn
from pibe_ext.settings import settings


__all__ = ("appconfig",)


class CallbackRegistry(list):
    def __call__(self):
        def func_decorator(func):
            self.append(func)
            return func
        return func_decorator


class AppConfig(object):

    def __init__(self):
        self.env = Env()
        self.env.read_env(os.environ.get("CONFIG_FILE", ".env"), recurse=False)
        self.settings = CallbackRegistry()
        self.initialize = CallbackRegistry()
        self.wsgi_middleware = CallbackRegistry()

    def _get_funcs(self, registry, **opts):
        funcs = [f for f in registry]

        only_fns = opts.get("only", [])
        if only_fns:
            funcs = [f for f in funcs if f.__name__ in only_fns]

        exclude_fns = opts.get("exclude", [])
        funcs = [f for f in funcs if f.__name__ not in exclude_fns]
        return funcs

    def init_settings(self, **opts):
        funcs = self._get_funcs(self.settings, **opts)
        settings.update(fn.merge(*[(f(**opts) or {}) for f in funcs]) or {})

    def init(self, **opts):
        if opts.get("initialize_settings", True):
            self.init_settings(**opts)

        funcs = self._get_funcs(self.initialize, **opts)
        for func in funcs:
            func(**opts)

    def start_app(self, app, **opts):
        if opts.get("initialize", True) == True:
            self.init(**opts)

        if opts.get("install_middleware", True) == True:
            for func in self.wsgi_middleware:
                app = func(app, **opts)

        return app


appconfig = AppConfig()
