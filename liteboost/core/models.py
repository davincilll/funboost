import typing

from liteboost.settings import settings


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
    task_id: str  # 任务id
    func_kwargs: dict  # 函数运行的任务参数
    func_path: str  # 函数路径
    func_name: str
    func_type: str  # 函数类型，单纯的函数，还是类方法，还是类静态方法，还是对象方法。

    pass
