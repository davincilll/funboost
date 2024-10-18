import importlib

from liteboost.core.enums import SchedulerConcurrentModeEnum

DEFAULTS = {
    "LOGGER": {
        "SAVE_LOG": True,  # 是否保存运行日志，在控制台发布
        "SAVE_LOG_LEVEL": "INFO",  # 日志级别
        "LOG_FILE_PATH": "",  # 日志文件路径
    },
    'BROKER': {
        # 这里的broker类型，需要去提供连接功能，消息的序列化和反序列化功能。。。。
        "BACKEND": "funboost.factories.consumer_factory.get_consumer",
        "LOCATION": "redis5://:J8689588@175.178.235.132:6379/0",
        "OPTIONS": {
        },
    },

    # 进行函数运行的一些持久化操作，默认为redis进行保存
    'PERSISTENCE': {
        "BACKEND": "funboost.factories.result_persistence_factory.get_result_persistence",
        "LOCATION": "",
        "OPTIONS": {},
    },
    # 这里的scheduler 还需要去完成获取所有
    'SCHEDULER': {
        "TIMEZONE": "Asia/Shanghai",
        "SAVE_STATUS": True,  # 是否保存函数的运行状态,使用DATABASES配置
        "SAVE_RESULT": True,  # 是否保存函数的运行结果,使用DATABASES配置
        "USE_DISTRIBUTED_FREQUENCY_CONTROL": True,  # 是否使用分布式控制频率
        "publisher_CLASS": "funboost.factories.publisher_factory.get_publisher",
        "CONSUMER_CLASS": "funboost.factories.consumer_factory.get_consumer",
        # 监控类，完成对所有当前存在的任务的捕获，以及心跳上报，获取所有的任务，任务启停，对任务中间状态的干涉等等。
        "MONITOR_CLASS": "funboost.factories.monitor_factory.get_monitor",
        "CONCURRENT": {
            # 这里的模式不能被覆写
            "MODE": SchedulerConcurrentModeEnum.THREAD,
            "CONCURRENT_POOL_CLASS": "",
            "OPTIONS": {},
        },
        "HEARTBEAT": {
            # 使用基于redis的心跳,默认是不开启的
            "ENABLE": False,
            "LOCATION": "",
            "OPTIONS": {},
        },
        # 默认的调度参数
        "DEFAULT_PARAMS": {
            #
            "USE_DISTRIBUTED_FREQUENCY_CONTROL": True,
            "AUTO_START_CONSUMING": True,
            "SUPPORT_REMOTE_KILL_TASK": True,
            "TASK_FILTER": True,
            "MSG_EXPIRE_SECONDS": None,
            "IS_USING_RPC_MODE": True, # 是否支持发布端获取函数运行结果
            "FUNCTION_TIMEOUT": 0,
            "MAX_RETRY_TIMES": 3,
            "PUSH_TO_DLX_QUEUE_WHEN_RETRY_MAX_TIMES": False,
        }
    },
}


class Settings:
    """
    A settings object that allows settings to be accessed as
    properties. Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, defaults=None):
        # Initialize with defaults and update with user settings
        self._settings = defaults or {}
        self._user_settings = self._load_user_settings()
        self._settings.update(self._user_settings)

        # Initialize cache for accessed attributes
        self._cached_attrs = set()

    @staticmethod
    def _load_user_settings():
        """Load user-defined settings from the configuration module."""
        settings_module = importlib.import_module('scheduler_config')
        return getattr(settings_module, 'FUN_SCHEDULER_SETTINGS', {})

    def update(self, new_settings):
        """Update settings with a dictionary of new settings."""
        self._settings.update(new_settings)

    def __repr__(self):
        return f"<Settings: {self._settings}>"


settings = Settings(DEFAULTS)
