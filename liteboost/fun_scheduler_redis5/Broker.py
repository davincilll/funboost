import redis5

from liteboost.core.brokers import BaseBroker
from liteboost.settings import settings


class RedisBroker(BaseBroker):
    """
    A RedisBroker class that manages message publishing and consuming using Redis.
    """

    def is_distributed_supported(self):
        return True

    def is_acked_supported(self):
        return True

    def is_windows_supported(self):
        return True

    def __init__(self):
        self.client = redis5.Redis.from_url = settings.BROCKER["LOCATION"]

    def get_client(self) -> redis5.Redis:
        """
        :rtype :redis5.Redis
        """
        return self.client

    def get_message(self):
        pass

    def put_message(self, msg):
        """
        :param msg:
        :return:
        """
        pass
