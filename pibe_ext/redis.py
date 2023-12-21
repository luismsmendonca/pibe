import funcy as fn
from .settings import settings
from walrus import *

__all__ = ("rdb",)


@fn.LazyObject
def rdb():
    return Database(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db
    )
