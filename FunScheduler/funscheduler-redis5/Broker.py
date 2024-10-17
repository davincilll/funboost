import redis5

from FunScheduler.core.brokers import BaseBroker
from FunScheduler.settings import settings


class RedisBroker(BaseBroker):
    """
    A RedisBroker class that manages message publishing and consuming using Redis.
    """

    def __init__(self):
        self.redis = redis5.Redis.from_url = settings.BROCKER["LOCATION"]

    def get_redis(self) -> redis5.Redis:
        """
        :rtype :redis5.Redis
        """
        return self.redis

    def get_message(self):
        pass

    def put_message(self, msg):
        """
        :param msg:
        :return:
        """
        pass




# 示例使用
if __name__ == "__main__":
    broker = RedisBroker()

    # 发布消息
    broker.publish('test_channel', {'event': 'test_event', 'data': 'Hello, World!'})


    # 定义回调函数
    def message_handler(message):
        print(f"Handling message: {message}")


    # 订阅消息（此调用会阻塞，直到手动停止）
    try:
        broker.subscribe('test_channel', message_handler)
    except KeyboardInterrupt:
        broker.close()
