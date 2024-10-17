import importlib

from FunScheduler.core.utils.module_loading import import_string
from FunScheduler.enums import SchedulerConcurrentModeEnum

DEFAULTS = {
    "LOGGER": {
        "SAVE_LOG": True,  # 是否保存运行日志，在控制台发布
        "SAVE_LOG_LEVEL": "INFO",  # 日志级别
        "LOG_FILE_PATH": "",  # 日志文件路径
    },
    'BROKER': {
        # 支持多个分组
        "default": {
            # 这里的broker类型，需要去提供连接功能，消息的序列化和反序列化功能。。。。
            "BACKEND": "funboost.factories.consumer_factory.get_consumer",
            "publisher_CLASS": "funboost.factories.publisher_factory.get_publisher",
            "CONSUMER_CLASS": "funboost.factories.consumer_factory.get_consumer",
            # 监控类，完成对所有当前存在的任务的捕获，以及心跳上报，获取所有的任务，任务启停，对任务中间状态的干涉等等。
            "MONITOR_CLASS": "funboost.factories.monitor_factory.get_monitor",
            "LOCATION": "",
            "OPTIONS": {},
        },
    },
    # 进行函数运行的一些持久化操作，默认为redis进行保存
    'PERSISTENCE': {
        # 分组可以在scheduler配置中进行切换，或者在局部配置中使用
        "default": {
            "BACKEND": "funboost.factories.result_persistence_factory.get_result_persistence",
            "LOCATION": "",
            "OPTIONS": {},
        }
    },
    # 这里的scheduler 还需要去完成获取所有
    'SCHEDULER': {
        "TIMEZONE": "Asia/Shanghai",
        "SAVE_STATUS": True,  # 是否保存函数的运行状态,使用DATABASES配置
        "SAVE_RESULT": True,  # 是否保存函数的运行结果,使用DATABASES配置
        "USE_DISTRIBUTED_FREQUENCY_CONTROL": True,  # 是否使用分布式控制频率
        "CONCURRENT": {
            # 这里的模式不能被覆写
            "MODE": SchedulerConcurrentModeEnum.THREAD,
            "CONCURRENT_POOL_CLASS": "",
            "OPTIONS": {},
        },
        # 默认的调度参数
        "DEFAULT_PARAMS": {
            "USE_DISTRIBUTED_FREQUENCY_CONTROL", True
        }
    },
}


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


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

    def _load_user_settings(self):
        """Load user-defined settings from the configuration module."""
        settings_module = importlib.import_module('scheduler_config')
        return getattr(settings_module, 'FUN_SCHEDULER_SETTINGS', {})

    def __getattr__(self, attr):
        if attr not in self._settings:
            raise AttributeError(f"Invalid setting: '{attr}'")

        # Try to get value from user settings or fall back to defaults
        val = self._settings.get(attr, self._settings[attr])
        # Coerce import strings into classes if necessary
        if self._is_import_path(attr):
            val = self._perform_import(val)
        # Cache the result
        return val

    @staticmethod
    def _is_import_path(name):
        """Check if the setting name indicates a valid import path."""
        return name == 'BACKEND' or name.endswith('CLASS')

    @staticmethod
    def _perform_import(val):
        """Import a class or module from a string path."""
        module_path, class_name = val.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def update(self, new_settings):
        """Update settings with a dictionary of new settings."""
        self._settings.update(new_settings)

    def __repr__(self):
        return f"<Settings: {self._settings}>"


settings = Settings(DEFAULTS)

if __name__ == '__main__':
    DEFAULTS = {}

    print(settings.LOGGER)

# settings = Settings(DEFAULTS)
