import funcy as fn
import msgpack
from walrus import *
from .settings import settings

__all__ = ("cache_db", "cache", "evict")

is_str = fn.isa(str)


@fn.LazyObject
def cache_db():
    return Walrus(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db
    )


@fn.decorator
def cache(call, *, key=None, evict_keys=None):
    req = call._args[0]
    key = (
        key
        if is_str(key)
        else key(call)
        if callable(key)
        else ":".join(
            [call._func.__name__]
            + fn.lmap(lambda x: f"{x[0]}-{x[1]}", req.params.items())
            + fn.lmap(lambda x: f"{x[0]}-{x[1]}", call._kwargs.items())
        )
    )
    key = f"catalog:cache:{key}"
    resp = cache_db.get(key)
    if resp:
        return msgpack.unpackb(resp, raw=False)

    lock = cache_db.lock(key, ttl=settings.cache_lock_duration)
    with lock:
        resp = call()
        cache_db[key] = msgpack.packb(resp, use_bin_type=True)
        evict_keys = (
            evict_keys
            if fn.is_list(evict_keys)
            else [evict_keys]
            if is_str(evict_keys)
            else evict_keys(call)
            if callable(evict_keys)
            else []
        )
        evict_keys = [ek.format(**call._kwargs) for ek in evict_keys]
        for evict_key in evict_keys:
            cache_set = cache_db.Set(f"catalog:eviction:{evict_key}")
            cache_set.add(key)

    return resp


@fn.decorator
def evict(call, *evict_keys):
    resp = call()
    for evict_key in evict_keys:
        evict_key = evict_key(call) if callable(evict_key) else evict_key
        evict_key = evict_key.format(**call._kwargs)
        cache_set = cache_db.Set(f"catalog:eviction:{evict_key}")
        for key in cache_set.members():
            cache_db.delete(key)
        cache_set.clear()
    return resp
