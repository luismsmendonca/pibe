import gevent
import logging
from funcy import wraps

__all__ = ('greenlet', 'infinite_loop', 'main_loop')

logger = logging.getLogger(__name__)

def greenlet(**kwargs):
    later = kwargs.get('later', None)
    repeat = kwargs.get('repeat', None)
    immediate = kwargs.get('immediate', False)

    def inner_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if repeat:
                def _repeat(func, *args, **kwargs):
                    logger.debug('Started repeating function {}'.format(func))
                    try:
                        if immediate:
                            gevent.spawn(func, *args, **kwargs)

                        while 1:
                            gevent.sleep(repeat)
                            gevent.spawn(func, *args, **kwargs)
                    except gevent.GreenletExit:
                        logger.debug('Stopped repeating function {}'.format(func))
                        pass
                gl_args = (_repeat, func, *args)
            else:
                gl_args = (func, *args)

            if later:
                gl = gevent.spawn_later(later, *gl_args, **kwargs)
            else:
                gl = gevent.spawn(*gl_args, **kwargs)
            return gl
        return wrapper
    return inner_wrapper


@greenlet()
def infinite_loop():
    while 1:
        gevent.sleep(0)

def main_loop():
    try:
        gevent.joinall([infinite_loop()])
    except (KeyboardInterrupt, SystemExit):
        pass
