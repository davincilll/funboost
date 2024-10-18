from typing import Any

from liteboost.core.brokers import BaseBroker


class BaseConsumer:
    """
    这个类是所有消费者类的基类，所有消费者类都要继承这个类。
    """
    # 使用的线程池
    threadPoolExecutor: Any
    broker: BaseBroker

    def load_config(self):
        pass

    def start(self):
        """
        完成系统配置，以及对系统配置的预处理，
        以非阻塞的方式启动dispatch的进行
        """
        pass

    def dispatch(self):
        """
        消费消息，这个方法由框架调用，用户无需重写。
        :param msg: 消息内容，类型为str。
        :return:
        """
        task_info = self.broker.get_task_info()
        # 符合条件就放到单独的线程中去等待，避免阻塞，等待完了之后再去调用submit_task
        # submit中去完成消费确认
        self.handle_timeout()
        self.handle_delay()
        self.handle_work_time()
        self.submit_task(task_info)

    def handle_work_time(self):
        """
        处理这条任务是否有规定工作时间
        """

    def handle_timeout(self):
        """
        处理这条消息的时间是否超时了
        """

    def handle_delay(self):
        """
        处理是否有延迟之类的情况
        """
        pass

    def submit_task(self, msg):
        """
        将消息传递给线程池进行消费
        """
        pass

    def consume(self, msg):
        """
        实际进行消费的地方，这里要完成消费，重试，放回死信队列等等功能
        """
        pass
