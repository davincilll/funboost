import inspect
import typing
from enum import Enum
from functools import wraps


class FuncTypeEnum(Enum):
    COMMON_FUNCTION = 'COMMON_FUNCTION'
    INSTANCE_METHOD = 'INSTANCE_METHOD'
    CLASS_METHOD = 'CLASS_METHOD'
    STATIC_METHOD = 'STATIC_METHOD'


class FuncInfo:
    def __init__(self, func_path: str, func_name: str, func_type: FuncTypeEnum, args_count: int, default_kwargs: dict = {}, ):
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

    def __init__(self, queue_name: str, max_retry_times: int = 3, msg_expire_seconds: typing.Union[float, int] = None, obj_init_params=None):
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
        if isinstance(func, staticmethod):
            return FuncTypeEnum.STATIC_METHOD
        elif isinstance(func, classmethod):
            return FuncTypeEnum.CLASS_METHOD
        elif hasattr(func, '__self__'):
            return FuncTypeEnum.INSTANCE_METHOD
        else:
            return FuncTypeEnum.COMMON_FUNCTION

    @staticmethod
    def _get_default_kwargs(func):
        """ 获取函数可接受的参数信息 """
        signature = inspect.signature(func)
        default_kwargs = {param.name: param.default for param in signature.parameters.values() if param.default is not param.empty}
        return default_kwargs

    @staticmethod
    def _get_args_count(func):
        """ 获取函数参数个数 """
        signature = inspect.signature(func)
        return len(signature.parameters)


# 使用示例
if __name__ == '__main__':
    @BoostParams(queue_name='task_queue', max_retry_times=5, msg_expire_seconds=60)
    def my_task_function(param1, param2):
        print(f"Executing task with {param1} and {param2}")


    tk = my_task_function
    print(tk)
