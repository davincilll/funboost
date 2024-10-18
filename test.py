from funboost.core.booster import Booster
from funboost.core.func_params_model import BoosterParams


class A:
    obj_init_params = {}
    @Booster(BoosterParams(queue_name='test_a'))
    def test(self, a):
        print(a)


if __name__ == '__main__':
    a = A()
    a.test.push(a, 1)
