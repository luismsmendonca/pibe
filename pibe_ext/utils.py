class lazy_object(object):
    """
    Create a proxy or placeholder for another object.
    """

    __slots__ = (
        "obj",
        "_callbacks",
        "_init_callback",
        "_check_and_initialize",
    )

    def __init__(self, init_callback=None):
        self._callbacks = []
        self._init_callback = init_callback
        self.initialize(None)

        def _check_and_initialize(self):
            if self.obj is None:
                if self._init_callback:
                    self.initialize(self._init_callback())
                else:
                    raise AttributeError("Cannot use uninitialized Proxy.")

        self._check_and_initialize = _check_and_initialize

    def initialize(self, obj):
        self.obj = obj
        for callback in self._callbacks:
            callback(obj)

    def attach_callback(self, callback):
        self._callbacks.append(callback)
        return callback

    def passthrough(method):
        def inner(self, *args, **kwargs):
            self._check_and_initialize(self)
            return getattr(self.obj, method)(*args, **kwargs)

        return inner

    # Allow proxy to be used as a context-manager.
    __enter__ = passthrough("__enter__")
    __exit__ = passthrough("__exit__")
    __call__ = passthrough("__call__")

    def __getattr__(self, attr):
        if attr not in self.__slots__:
            self._check_and_initialize(self)
        return getattr(self.obj, attr)

    def __setattr__(self, attr, value):
        if attr not in self.__slots__:
            raise AttributeError("Cannot set attribute on proxy.")

        return super(lazy_object, self).__setattr__(attr, value)

    def __getitem__(self, key):
        self._check_and_initialize(self)
        return self.obj.__getitem__(key)

    def __setitem__(self, key, value):
        self._check_and_initialize(self)
        return self.obj.__setitem__(key, value)
