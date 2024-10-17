import typing

from fun_scheduler.settings import settings


class BoostParams:
    queue_name: str
    max_retry_times: int
    msg_expire_seconds: typing.Union[float, int]

    def __init__(self, queue_name: str, max_retry_times: int = 3, msg_expire_seconds: typing.Union[float, int] = None):
        self.default_boost_params = settings.SCHEDULER["DEFAULT_PARAMS"]
        # 进行初始化

class PublishParams:
    pass

class ConsumeParams:
    pass

class TaskInfo:
    """
    记录任务信息
    """
    pass