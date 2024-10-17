import abc

from FunScheduler.settings import settings


class BaseBroker():

    def get_message(self):
        pass

    def put_message(self, msg):
        """
        :param msg:
        :return:
        """
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
