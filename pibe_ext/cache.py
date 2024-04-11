import funcy as fn
import msgpack
from walrus import *
from .appconfig import appconfig
from .settings import settings

__all__ = ("cachedb", "cache", "evict")

is_str = fn.isa(str)


@appconfig.settings()
def cache_settings(**opts):
    return {
        "cache_host": appconfig.env.str("REDIS_HOST", "localhost"),
        "cache_port": appconfig.env.int("REDIS_PORT", 6379),
        "cache_db": appconfig.env.int("CACHE_DB", 0),
        "cache_lock_duration": appconfig.env.int("CACHE_LOCK_DURATION", 500),  # in milliseconds
    }


@fn.LazyObject
def cachedb():
    return Database(
        host=settings.cache_host,
        port=settings.cache_port,
        db=settings.cache_db
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
    resp = cachedb.get(key)
    if resp:
        return msgpack.unpackb(resp, raw=False)

    lock = cachedb.lock(key, ttl=settings.cache_lock_duration)
    with lock:
        resp = call()
        cachedb[key] = msgpack.packb(resp, use_bin_type=True)
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
            cache_set = cachedb.Set(f"catalog:eviction:{evict_key}")
            cache_set.add(key)

    return resp


@fn.decorator
def evict(call, *evict_keys):
    resp = call()
    for evict_key in evict_keys:
        evict_key = evict_key(call) if callable(evict_key) else evict_key
        evict_key = evict_key.format(**call._kwargs)
        cache_set = cachedb.Set(f"catalog:eviction:{evict_key}")
        for key in cache_set.members():
            cachedb.delete(key)
        cache_set.clear()
    return resp
