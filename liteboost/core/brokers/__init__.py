import abc

from liteboost.core.models import TaskInfo
from liteboost.settings import settings


class BaseBroker:
    task_info: dict
    json_msg: str

    def get_task_info(self):
        json_msg = self.get_message()
        return TaskInfo.from_json(json_msg)

    def put_task_info(self, task_info: TaskInfo):
        """
        :param task_info:
        :return:
        """
        msg = task_info.to_json()
        self.put_message(msg)

    @abc.abstractmethod
    def get_message(self):
        """
        从broker中获取真正的消息体，比如从rabbitmq中获取的是一个完整的消息体，但是从kafka中获取的是一个key，需要通过这个key去获取真正的消息体
        :return:
        """
        pass

    @abc.abstractmethod
    def put_message(self, msg):
        """
        将消息体放入broker中，比如将一个完整的消息体放入rabbitmq中，将一个key放入kafka中。
        :param msg:
        :return:
        """
        pass

    @abc.abstractmethod
    def ack_message(self, msg):
        pass

    @abc.abstractmethod
    def is_distributed_supported(self):
        """
        是否支持分布式
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_acked_supported(self):
        """
        是否支持消息确认模式
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_windows_supported(self):
        """
        是否支持windows环境
        """
        raise NotImplementedError

    @staticmethod
    def is_distributed_frequency_control_supported(self):
        """
        分布式并发控制是否支持当前broker
        :return:
        """
        return settings.HEARTBEAT["ENABLE"]
