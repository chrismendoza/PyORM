class Event(object):
    listeners = {}

    @classmethod
    def register_listener(cls, event, listener):
        """
            Remove a listener for a specified event
                Expects a unicode/string event, listener method/function
        """
        if isinstance(event, basestring):
            if event not in Event.listeners:
                Event.listeners[event] = []
            Event.listeners[event].append(listener)

    @classmethod
    def remove_listener(cls, event, listener):
        """
            Remove a listener for a specified event
                Expects a unicode/string event, listener method/function
        """
        if isinstance(event, basestring):
            if event not in Event.listeners:
                Event.listeners[event] = []
            try:
                del(Event.listeners[event][Event.listeners[
                    event].index(listener)])
            except:
                pass

    @classmethod
    def fire(cls, event, args, kwargs, response=None):
        """
            Fires an event, passing an object or None if there is no object,
            so that the plugin has the ability to modify the object of the
            method signaling the event.
        """
        if isinstance(event, basestring):
            if event.startswith('pre'):
                for listener in cls.listeners.get(event, []):
                    args, kwargs = listener(args, kwargs)
                return {'args': args, 'kwargs': kwargs}
            else:
                for listener in cls.listeners.get(event, []):
                    response = listener(args, kwargs, response)
                return response


def event_decorator(*eargs):
    """
        Event decorator, used for 2 types of events:
            'pre': called prior to a method with the @Event decorator being called.
                Is only allowed to alter the environment and the args passed to the
                decorated method/function.
            'post': called after a method with the @Event decorator has been called.
                Is only allowed to alter the environment and the args passed to the
                decorated method/function.
    """
    if len(eargs) and callable(eargs[0]):
        func = eargs[0]
        name = func.__name__

        def wrapper(*args, **kwargs):
            preresponse = Event.fire('pre{0}'.format(name), args, kwargs)
            response = func(
                *preresponse.get('args', ()), **preresponse.get('kwargs', {}))
            response = Event.fire(
                'post{0}'.format(name), args, kwargs, response)
            return response
        return wrapper
    else:
        name = eargs[0]

        def func_wrapper(func):
            def wrapper(*args, **kwargs):
                preresponse = Event.fire('pre{0}'.format(name), args, kwargs)
                response = func(*preresponse.get(
                    'args', ()), **preresponse.get('kwargs', {}))
                response = Event.fire(
                    'post{0}'.format(name), args, kwargs, response)
                return response
            return wrapper
        return func_wrapper
