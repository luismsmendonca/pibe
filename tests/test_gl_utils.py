
import gevent
from gl_utils import *
from unittest.mock import Mock

def test_decorator():

    @greenlet()
    def foo():
        return 'bar'

    r = foo()

    assert type(r) == gevent.Greenlet
    gl1 = foo()
    gevent.joinall([gl1])
    assert gl1.value == 'bar'

    mock1 = Mock()

    @greenlet(later=0.1)
    def bar(_mock):
        _mock()

    gl2 = bar(mock1)
    gevent.sleep(0.2)
    # assert mock1.called
    # import pdb; pdb.set_trace()
    assert mock1.call_count == 1

    mock2 = Mock()

    @greenlet(repeat=0.1)
    def fooz(_mock):
        if _mock.call_count < 4:
            _mock()
        else:
            raise gevent.GreenletExit

    gl3 = fooz(mock2)
    gevent.sleep(1)
    # assert mock1.called
    # import pdb; pdb.set_trace()
    assert mock2.call_count == 4
    # gevent.sleep(0.2)
    # assert False
