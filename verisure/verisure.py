from verisure.session import Session


def parse_result(type):
    def inner(func):
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            parsed = type(res)
            return parsed
        return wrapper
    inner.is_query = True
    return inner

class SmartPlug:
    def __init__(self, smartplug_data) -> None:
        self.device_label = smartplug_data["device"]["deviceLabel"]
        self.is_on = smartplug_data["currentState"] == "ON"
    

class Verisure(Session):
    pass

Verisure.smartplug = parse_result(Verisure.smartplug)
Verisure.smartplug.__doc__ = Session.smartplug.__doc__
Verisure.smartplug.__annotations__ = Session.smartplug.__annotations__