import logging
from .http import http, no_content

logger = logging.getLogger(__name__)

__all__ = ("webhook",)


class WebhookRegistry(dict):
    rollback_fns = dict()

    def register(self, wh_name):
        def func_decorator(func):
            if wh_name not in self:
                self[wh_name] = []
            self[wh_name].append(func)
            return func

        return func_decorator

    def rollback(self, wh_name):
        def func_decorator(func):
            if wh_name not in self.rollback_fns:
                self.rollback_fns[wh_name] = []
            self.rollback_fns[wh_name].append(func)
            return func

        return func_decorator

    def commit(self, wh_name, *args, **kwargs):
        try:
            for func in self.get(wh_name, []):
                func(*args, **kwargs)
        except:
            for rb_func in self.rollback_fns.get(wh_name, []):
                rb_func(*args, **kwargs)
            raise

webhook = WebhookRegistry()
