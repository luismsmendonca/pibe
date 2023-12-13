import os
import logging
import funcy as fn
from types import SimpleNamespace

__all__ = ("settings",)

class SettingsRegistry(SimpleNamespace):
    default_fns = []

    def defaults(self):
        def func_decorator(func):
            self.default_fns.append(func)
            return func
        return func_decorator

    def get_defaults(self, **opts):
        exec_fns = [f for f in self.default_fns]
        skip = opts.get("skip", [])
        if skip:
            exec_fns = [f for f in exec_fns if f.__name__ not in skip]

        only = opts.get("only", [])
        if only:
            exec_fns = [f for f in exec_fns if f.__name__ in only]

        return fn.merge(*[f(**opts) for f in exec_fns])

    def initialize(self, **opts):
        self.__dict__.update(self.get_defaults(**opts) or {})

    def get(self, *args):
        return self.__dict__.get(*args)


settings = SettingsRegistry()
