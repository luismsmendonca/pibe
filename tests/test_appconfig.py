from pibe_ext.appconfig import AppConfig
from unittest.mock import MagicMock

class FunctionMagicMock(MagicMock):
    __name__ = "name"

def test_appconfig():
    ac = AppConfig()

    sf1 = FunctionMagicMock()
    ac.settings.append(sf1)

    sf2 = FunctionMagicMock()
    ac.initialize.append(sf2)

    sf3 = FunctionMagicMock()
    ac.wsgi_middleware.append(sf3)

    ac.start_app(MagicMock())

    assert sf1.called
    assert sf2.called
    assert sf3.called
    # sf.reset_mock()
    #
    # assert sf.called

    
