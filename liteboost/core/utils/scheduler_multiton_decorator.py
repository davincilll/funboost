import threading
from functools import wraps


def SynchronizedQueueMultiton():  # noqa
    """
    使用在Scheduler上，以魔术的形式，将一个类方法，动态的根据queue_name去维护一个内部的多例，
    并根据id去找到或创建对应的Scheduler实例，替换cls为instance去执行
    """
    lock = threading.Lock()
    def decorator(class_method):
        @wraps(class_method)
        def wrapper(cls, *args, **kwargs):
            with lock:

            return class_method(instance, *args, **kwargs)

        return wrapper

    return decorator