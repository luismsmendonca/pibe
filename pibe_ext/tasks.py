import os
import json
import time
import funcy as fn
import threading
import queue
import logging
from redis import Redis

from pibe_ext.appconfig import *
from pibe_ext.settings import *
from pibe_ext.http import *
from pibe_ext.validator import *


__all__ = ("task",)

logger = logging.getLogger(__name__)

q = queue.Queue()

@appconfig.settings()
def task_settings(**opts):
    return {
        "tasks_sync_exec": appconfig.env.bool("TASKS_SYNC_EXEC", False),
        "tasks_redis_host": appconfig.env.str("REDIS_HOST", "localhost"),
        "tasks_redis_port": appconfig.env.int("REDIS_PORT", 6379),
        "tasks_redis_db": appconfig.env.bool("TASKS_REDIS_DB", 0),
        "tasks_redis_queue_name": appconfig.env("TASKS_REDIS_QUEUE_NAME", "tasks"),
    }


@fn.LazyObject
def tasksdb():
    return Redis(
        host=settings.tasks_redis_host,
        port=settings.tasks_redis_port,
        db=settings.tasks_redis_db
    )


class TaskWrapper(object):
    def __init__(self, func, task_name):
        self.func = func
        self.task_name = task_name

    def __call__(self, *args, **kwargs):
        if settings.tasks_sync_exec:
            self.func(*args, **kwargs)
        else:
            enqueue({
                "task": self.task_name,
                "args": args,
                "kwargs": kwargs,
            })


class TaskRegistry(dict):
    def __call__(self, name=None):
        def func_decorator(func):
            task_name = name or func.__name__
            self[task_name] = func
            return TaskWrapper(func, task_name)
        return func_decorator


task = TaskRegistry()


class Worker(threading.Thread):
    def __init__(self, q, n, *args, **kwargs):
        self.q = q
        self.n = n
        super().__init__(*args, **kwargs)

    def run(self):
        logger.info(f"[{threading.current_thread().name}] Starting Worker {self.n}")
        while True:
            try:
                payload = self.q.get(timeout=1)
            except queue.Empty:
                continue

            task_name = payload["task"]
            args = payload["args"]
            kwargs = payload["kwargs"]
            task_fn = task[task_name]
            try:
                t0 = time.time()
                task_fn(*args, **kwargs)
                elapsed = time.time() - t0
                logger.info(f"[{threading.current_thread().name}] [Worker {self.n}] [task={payload['task']} args={args} args={kwargs}] executed in {elapsed} seconds")
            except Exception as e:
                logger.exception(f"[{threading.current_thread().name}] [Worker {self.n}] [task={payload['task']} args={args} args={kwargs}] Error executing task.", exc_info=True)

            self.q.task_done()


class WorkerOrchestrator(threading.Thread):
    def __init__(self, q, *args, **kwargs):
        self.q = q
        super().__init__(*args, **kwargs)

    def run(self):
        logger.info(f"[{threading.current_thread().name}] Starting Worker Orchestrator [PID={os.getpid()}]")
        while True:
            msg = tasksdb.rpop(settings.tasks_redis_queue_name)
            if msg is None:
                time.sleep(0.1)
                continue

            payload = json.loads(msg)
            q.put_nowait(payload)


def runworkers(total_threads=3):
    threads = [WorkerOrchestrator(q)] + [Worker(q, n+1) for n in range(total_threads)]
    [t.start() for t in threads]
    [t.join() for t in threads]


def enqueue(payload):
    tasksdb.rpush(settings.tasks_redis_queue_name, json.dumps(payload))
