from enum import Enum


# 补充一些对部分配置的枚举
class SchedulerConcurrentModeEnum(Enum):
    THREAD = 'thread'
    PROCESS = 'process'
    ASYNCIO = 'asyncio'
    SINGLE = 'single'
    GEVENT = 'gevent'
    GEVENT_EVENTLET = 'gevent_eventlet'


"""
FunScheduler 是一个中心化的定时任务框架，相较于funboost的完全分布式框架，将职责进行了分离，分离出了scheduler、producer、consumer三个核心组件，
scheduler负责调度任务，producer负责发布任务，consumer负责消费任务。
相较于funboost的每个函数一个booster（内部包括消费者和生产者）？？？,使用装饰器将函数注册为booster，每一个都要单独去启动发布和消费
FunScheduler在每一个进程维护一个Scheduler，用于控制整个框架的调度，对于任意函数的调度，需要将函数对象，以及函数的参数传递给全局单例的Scheduler，
由Scheduler去调度producer的启动将任务信息投递给Broker，然后由Scheduler启动consumer接受对应的任务信息完成任务的消费。。
"""

FUN_SCHEDULER_SETTINGS = {
    # 默认的调度器，以及对应的生产者，消费者配置
    # 后面再写其他类型的调度器，目前只使用默认的 Scheduler
    "LOGGER": {
        "SAVE_LOG_LEVEL": "INFO",  # 日志级别
        "LOG_FILE_PATH": "",  # 日志文件路径
    },
    # 默认的中间件,中间件只负责连接，不负责具体的任务，至于是否支持分布式，是否支持消费确认等功能由生产者消费者去提供，
    # 并向SCHEDULER进行声明，SCHEDULER默认认为其声明的结果是可靠的,并调用其实现的功能。
    # 这里做成插件包，完成对多种中间件的支持
    'DEFAULT_BROKER': {
        # 这里的broker类型，需要去提供连接功能，消息的序列化和反序列化功能。。。。
        "BROKER_BACKEND": "funboost.factories.consumer_factory.get_consumer",
        "PRODUCER_CLASS": "funboost.factories.producer_factory.get_producer",
        "CONSUMER_CLASS": "funboost.factories.consumer_factory.get_consumer",
        # 监控类，完成对所有当前存在的任务的捕获，以及心跳上报，获取所有的任务，任务启停，对任务中间状态的干涉等等。
        "MONITOR_CLASS": "funboost.factories.monitor_factory.get_monitor",
        "LOCATION": "",
        "OPTIONS": {},
    },
    # 进行函数运行的一些持久化操作，默认为本地sqlite保存
    'DEFAULT_DATABASES': {
        "BACKEND": "funboost.factories.result_persistence_factory.get_result_persistence",
        "LOCATION": "",
        "OPTIONS": {},
    },
    # 这里的scheduler 还需要去完成获取所有
    'SCHEDULER': {
        "TIMEZONE": "Asia/Shanghai",
        "SAVE_LOG": True,  # 是否保存运行日志
        "SAVE_STATUS": True,  # 是否保存函数的运行状态,使用DATABASES配置
        "SAVE_RESULT": True,  # 是否保存函数的运行结果,使用DATABASES配置
        "CONCURRENT": {
            "MODE": SchedulerConcurrentModeEnum.THREAD,
            "CONCURRENT_POOL_CLASS": "",
            "OPTIONS": {},
        },
    },
}
