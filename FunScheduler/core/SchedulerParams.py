import typing


class SchedulerParams:
    queue_name: str
    max_retry_times: int
    msg_expire_senconds: typing.Union[float, int]
