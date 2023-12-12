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
        return fn.merge(*[default_fn(**opts) for default_fn in self.default_fns])

    def initialize(self, **opts):
        self.__dict__.update(self.get_defaults(**opts) or {})

    def get(self, *args):
        return self.__dict__.get(*args)

settings = SettingsRegistry()
