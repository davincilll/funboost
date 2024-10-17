# 补充一些对部分配置的枚举
from enum import Enum


class SchedulerConcurrentModeEnum(Enum):
    THREAD = 'thread'
    ASYNCIO = 'asyncio'
    SINGLE = 'single'
    GEVENT = 'gevent'
    GEVENT_EVENTLET = 'gevent_eventlet'


