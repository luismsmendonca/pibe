from pibe import DotDict


def test_dotdict():
    d1 = DotDict()

    assert d1 == {}

    d1["dummy"] = 1
    assert d1.dummy == 1

    d1.update({"foo": "bar"})
    assert d1.foo == "bar"


    d2 = DotDict({})
    d2.update({"foo": "bar"})
    assert d2.foo == "bar"
    assert d2["foo"] == "bar"
