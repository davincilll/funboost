from time import sleep

from funboost.constant import BrokerEnum

from funboost.core.booster import Booster
from funboost.core.func_params_model import BoosterParams, PriorityConsumingControlConfig


class A:
    obj_init_params = {}

    @Booster(BoosterParams(queue_name='test_a'))
    def test(self, a):
        print(a)

@Booster(BoosterParams(queue_name='test_b',broker_kind = BrokerEnum.SQLITE_QUEUE))
def test_b(b):
    print(b)


if __name__ == '__main__':
    # a = A()
    # 这里只管发送，各种各样的额外信息是消费者处理的事情
    test_b.publish({'b': 2},priority_control_config = PriorityConsumingControlConfig(countdown=10))
    test_b.consume()
    while True:
        sleep(10)
    # a.test.push(a,1)
    # a.test.publish({'self':a, 'a':1},)
