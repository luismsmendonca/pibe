import os
import logging
from environs import Env
import funcy as fn
from pibe_ext.settings import settings


__all__ = ("appconfig",)


class InitializationRegistry(list):
    def __call__(self):
        def func_decorator(func):
            self.append(func)
            return func
        return func_decorator


class AppConfig(object):
    settings = InitializationRegistry()
    initialize = InitializationRegistry()
    wsgi_middleware = InitializationRegistry()

    def __init__(self):
        self.env = Env()
        self.env.read_env(os.environ.get("CONFIG_FILE", ".env"), recurse=False)

    def start_app(self, app, **opts):

        if opts.get("initialize", True) == True:
            _settings = fn.merge(*[(f(**opts) or {}) for f in self.settings]) or {}
            settings.__dict__.update(_settings)
            for f in self.initialize:
                f(**opts)

        if opts.get("install_middleware", True) == True:
            for f in self.wsgi_middleware:
                app = f(app, **opts)

        return app


appconfig = AppConfig()
