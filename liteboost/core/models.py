import inspect
import json
import typing
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from functools import wraps

from pydantic import BaseModel

from funboost import Booster


class BaseJsonAbleModel(BaseModel):
    """
    因为model字段包括了 函数和自定义类型的对象,无法直接json序列化,需要自定义json序列化
    """

    def get_str_dict(self) -> dict:
        model_dict: dict = self.dict()  # noqa
        model_dict_copy = OrderedDict()
        # 填充model_dict_copy
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
            elif type(v).__module__ != "builtins":  # 自定义类型的对象,json不可序列化,需要转化下.
                model_dict_copy[k] = str(v)
            else:
                model_dict_copy[k] = v
        return model_dict_copy

    def json_str_value(self) -> str:
        """
        json序列化
        """
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, )
        except TypeError as e:
            return str(self.get_str_dict())

    def update_from_dict(self, dictx: dict):
        """
        从字典中更新属性
        """
        for k, v in dictx.items():
            setattr(self, k, v)
        return self

    def update_from_kwargs(self, **kwargs):
        """
        从kwargs中更新属性
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def update_from_model(self, modelx: BaseModel):
        """
        从另一个model中更新属性
        """
        for k, v in modelx.model_dump().items():
            setattr(self, k, v)
        return self

    @staticmethod
    def init_by_another_model(model_type: typing.Type[BaseModel], modelx: BaseModel):
        init_dict = {}
        for k, v in modelx.model_dump().items():
            if k in model_type.model_fields.keys():
                init_dict[k] = v
        return model_type(**init_dict)

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"


class FuncTypeEnum(Enum):
    COMMON_FUNCTION = 'COMMON_FUNCTION'
    INSTANCE_METHOD = 'INSTANCE_METHOD'
    CLASS_METHOD = 'CLASS_METHOD'
    # STATIC_METHOD = 'STATIC_METHOD' # 静态方法与COMMON方法是等同的


class FuncInfo(BaseJsonAbleModel):
    """
    函数信息，用于在函数被装饰的时候，自动记录函数路径，函数名，函数类型，函数参数个数，默认参数等。
    """
    func_path: str  # 函数路径
    func_name: str  # 函数名字
    func_type: FuncTypeEnum  # 函数类型
    default_kwargs: dict  # 函数默认参数
    args_count: int  # 函数位置参数格式

    def __repr__(self):
        return (f"FuncInfo(func_path={self.func_path}, func_name={self.func_name}, "
                f"func_type={self.func_type}, func_kwargs={self.func_kwargs})")


class PriorityBoostParams(BaseJsonAbleModel):
    """
    在进行publish时，对BoostParams优先级更高的运行参数，也包括了定时任务方面的参数
    """
    function_timeout: typing.Union[float, int] = 0  # 函数超时时间,为0是不限制,超时会进行杀死
    max_retry_times: int = None  # 重试次数
    msg_expire_seconds: int = None  # 消息过期时间，消费者接受后判断是否过期，过期则进行丢弃。
    rpc_mode: bool = None  # 发送方是否可以获取到结果
    countdown: typing.Union[float, int] = None  # 发布多少秒后执行
    eta: datetime = None  # 定时什么时候执行
    broker_extra_config: dict = None  # 中间件支持的其他配置


class BoostParams(BaseJsonAbleModel):
    """
    为装饰的函数自动注册 BoostParams 参数和 FuncInfo 信息
    """
    max_retry_times: int
    msg_expire_seconds: typing.Union[float, int]
    # 对于实例方法，需要传递broker_group
    obj_init_params: dict
    broker_group: str
    broker_extra_config: dict = {}  # 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
    # 例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，有的中间件原生能支持消息优先级有的中间件不支持,每一种消息队列都有独特的配置参数意义，可以通过这里传递。每种中间件能传递的键值对可以看consumer类的 BROKER_EXCLUSIVE_CONFIG_DEFAULT
    persistence_handler_group: str
    concurrent_num: int = 50  # 并发数量，并发种类由concurrent_mode决定
    qps: typing.Union[float, int] = None
    use_distributed_frequency_control: bool = False
    send_consumer_heartbeat_to_redis: bool = False
    max_retry_times: int = 3
    retry_interval_seconds: typing.Union[float, int] = 0
    push_to_dlx_queue_when_retry_max_times: bool = False  # 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。
    function_timeout: typing.Union[int, float] = 0  # 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。 谨慎使用,非必要别去设置超时时间,设置后性能会降低(因为需要把用户函数包装到另一个线单独的程中去运行),而且突然强制超时杀死运行中函数,可能会造成死锁.(例如用户函数在获得线程锁后突然杀死函数,别的线程再也无法获得锁了)
    msg_expire_seconds: typing.Union[float, int] = None  # 消息过期时间,可以设置消息是多久之前发布的就丢弃这条消息,不运行. 为None则永不丢弃
    task_filter: bool = False  # 是否对函数入参进行过滤去重.
    task_filter_expire_seconds: int = 0  # 任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ， 30分钟前发布过1 + 2 的任务，现在仍然执行，如果是30分钟以内执行过这个任务，则不执行1 + 2
    rpc_mode: bool = False  # 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。
    rpc_result_expire_seconds: int = 600  # 保存rpc结果的过期时间.
    remote_kill_task: bool = False  # 是否支持远程任务杀死功能，如果任务数量少，单个任务耗时长，确实需要远程发送命令来杀死正在运行的函数，才设置为true，否则不建议开启此功能。(是把函数放在单独的线程中实现的,随时准备线程被远程命令杀死,所以性能会降低)
    not_run_by_specify_time_effect: bool = False  # 是否使不运行的时间段生效
    run_by_specify_time: tuple = ('10:00:00', '22:00:00')  # 不运行的时间段,在这个时间段自动不运行函数。
    auto_start_consuming_message: bool = False  # 是否在定义后就自动启动消费，无需用户手动写 .consume() 来启动消息消费。


class Task:
    """
    Task 注解，标注这个是一个任务Task
    # 可以传递的参数有queue_name,BoostParams，建立一个booster实例
    # booster实例包括BoostParams和FuncInfo
    # booster在初始化的时候也需要根据BoostParams和FuncInfo参数build 消费者发布者持久化组broker等等。
    # 在scheduler中 add_task 的时候可以动态的添加函数的参数，以及boostParams的覆盖，这些是动态参数
    # 在scheduler中，add_task 根据函数对象的属性找到对应的booster，并调用其发布任务。
    # booster的静态注册通过扫描机制来完成，从而在多个运行钩子中，定位到对应的booster，当运行时通过queue_name找到对应的booster进行启动
    # scheduler中的注册表包括，queue_name,func,booster,在静态扫描注册的过程中完成。
    # 新增queue的时候会共用booster
    """
    queue_name: str
    boost_params: BoostParams

    def build_booster(self, func: typing.Callable, boost_params: BoostParams) -> Booster:
        pass

        def get_func_info(self, func):
            """
            根据函数func生成func_info
            """
            func_type = self._get_func_type(func)
            default_kwargs = self._get_default_kwargs(func)
            args_count = self._get_args_count(func)
            return FuncInfo(
                func_path=func.__module__ + '.' + func.__qualname__,
                func_name=func.__name__,
                func_type=func_type,
                default_kwargs=default_kwargs,  # 存储参数默认值信息
                args_count=args_count,
            )

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


class TaskInfo(BaseJsonAbleModel):
    """
    用于在消息队列中存储任务信息的
    """
    task_id = None
    # todo:后续为了控制消息大小，将BoostParams中值得传递的消息提炼出来放到另外一个模型中进行传递
    priority_boost_params: PriorityBoostParams = None
    func_info: dict = None  # 函数的运行参数

    @staticmethod
    def from_json(s: str):
        """从 JSON 字符串反序列化为 TaskInfo 实例"""
        data = json.loads(s)
        if 'boost_params' in data:
            data['boost_params'] = BoostParams.from_dict(data['boost_params'])  # 转换回 BoostParams 对象
        return TaskInfo(**data)

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
