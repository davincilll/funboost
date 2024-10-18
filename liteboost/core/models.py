import inspect
import json
import typing
from enum import Enum
from functools import wraps


class FuncTypeEnum(Enum):
    COMMON_FUNCTION = 'COMMON_FUNCTION'
    INSTANCE_METHOD = 'INSTANCE_METHOD'
    CLASS_METHOD = 'CLASS_METHOD'
    # STATIC_METHOD = 'STATIC_METHOD' # 静态方法与COMMON方法是等同的


class FuncInfo:
    def __init__(self, func_path: str, func_name: str, func_type: FuncTypeEnum, args_count: int,
                 default_kwargs: dict = {}, ):
        self.func_path = func_path
        self.func_name = func_name
        self.func_type = func_type
        self.func_kwargs = default_kwargs
        self.args_count = args_count

    def __repr__(self):
        return (f"FuncInfo(func_path={self.func_path}, func_name={self.func_name}, "
                f"func_type={self.func_type}, func_kwargs={self.func_kwargs})")


class BoostParams:
    """
    为装饰的函数自动注册 BoostParams 参数和 FuncInfo 信息
    """

    def __init__(self, queue_name: str, max_retry_times: int = 3, msg_expire_seconds: typing.Union[float, int] = None,
                 obj_init_params=None):
        self.queue_name = queue_name
        self.max_retry_times = max_retry_times
        self.msg_expire_seconds = msg_expire_seconds
        self.obj_init_params = obj_init_params

    def __repr__(self):
        return (f"BoostParams(queue_name={self.queue_name}, "
                f"max_retry_times={self.max_retry_times}, msg_expire_seconds={self.msg_expire_seconds})")

    def __call__(self, func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 自动生成 FuncInfo
        func_type = self._get_func_type(func)
        default_kwargs = self._get_default_kwargs(func)
        args_count = self._get_args_count(func)

        if func_type == FuncTypeEnum.INSTANCE_METHOD and self.obj_init_params is None:
            raise ValueError("对于类的实例化方法，需要在BoostParams中传递obj_init_params以供在分布式环境中进行执行")
        func_info = FuncInfo(
            func_path=func.__module__ + '.' + func.__qualname__,
            func_name=func.__name__,
            func_type=func_type,
            default_kwargs=default_kwargs,  # 存储参数默认值信息
            args_count=args_count,
        )
        # 将 BoostParams 实例和 FuncInfo 添加到函数
        wrapper.boost_params = self
        wrapper.func_info = func_info

        return wrapper

    @staticmethod
    def _get_func_type(func):
        """ 判断函数的类型并返回对应的 FuncTypeEnum """
        # 获取函数的参数列表
        signature = inspect.signature(func)
        params = list(signature.parameters.keys())
        if params and params[0] == 'cls':
            return FuncTypeEnum.CLASS_METHOD
        elif params and params[0] == 'self':
            return FuncTypeEnum.INSTANCE_METHOD
        return FuncTypeEnum.COMMON_FUNCTION

    @staticmethod
    def _get_default_kwargs(func):
        """ 获取函数可接受的参数信息 """
        signature = inspect.signature(func)
        default_kwargs = {param.name: param.default for param in signature.parameters.values() if
                          param.default is not param.empty}
        return default_kwargs

    @staticmethod
    def _get_args_count(func):
        """ 获取函数参数个数 """
        signature = inspect.signature(func)
        return len(signature.parameters)


class PublishParams:
    """
    看看是如何实现分布式场景下精准实现控频的，以及是如何实现延迟消费的，以及是如何实现定时消费的
    """


class TaskInfo:
    """
    用于在消息队列中存储任务信息的
    """
    task_id = None
    boost_params: BoostParams = None
    func_kwargs: dict = None  # 函数的运行参数

    # todo:完成序列化方法
    def to_json(self):
        """将实例属性序列化为 JSON 字符串"""
        data = self.__dict__.copy()  # 复制实例字典
        if isinstance(self.boost_params, BoostParams):
            data['boost_params'] = self.boost_params.to_dict()  # 转换为字典
        return json.dumps(data)

    @staticmethod
    def from_json(s: str):
        """从 JSON 字符串反序列化为 TaskInfo 实例"""
        data = json.loads(s)
        if 'boost_params' in data:
            data['boost_params'] = BoostParams.from_dict(data['boost_params'])  # 转换回 BoostParams 对象
        return TaskInfo(**data)

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d: dict):
        return TaskInfo(**d)


# 使用示例
if __name__ == '__main__':
    @BoostParams(queue_name='task_queue', max_retry_times=5, msg_expire_seconds=60)
    def my_task_function0(param1, param2):
        print(f"Executing task with {param1} and {param2}")


    class Test:
        # @BoostParams(queue_name='task_queue', max_retry_times=5, msg_expire_seconds=60)
        def my_task_function1(self, param1, param2):
            print(f"Executing task with {param1} and {param2}")

        @classmethod
        @BoostParams(queue_name='task_queue', max_retry_times=5, msg_expire_seconds=60)
        def my_task_function2(cls, param2):
            print(f"Executing task with {param2}")

        @staticmethod
        @BoostParams(queue_name='task_queue', max_retry_times=5, msg_expire_seconds=60)
        def my_task_function3(param1):
            print(f"Executing task with {param1}")


    tk = my_task_function0
    tk1 = Test().my_task_function1
    tk2 = Test.my_task_function2
    tk3 = Test.my_task_function3
    print(tk)
    print(tk2)
    print(tk3)
