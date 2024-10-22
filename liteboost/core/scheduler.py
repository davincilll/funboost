import importlib
import inspect
import os
import typing

from liteboost.core.models import BoostParams, PriorityBoostParams


class Scheduler:
    """
    这里会维护一张表去完成存在的queue和Booster以及函数的对应关系。
    可以使用自动扫描机制，扫描静态的Booster。但是如何在分布式环境下如何维护动态的Booster。
    """
    """
    以非装饰器的方式运行，在运行的时候传递覆盖运行参数以及函数参数进行消费信息的投递，
    这里需要保证后续变更中函数的位置不变，
    scheduler只负责启动发布和消费
    """
    # 用queue_name 作为键名，存储scheduler,用于支持用户自定义的broker和persistence_handler
    # 关于函数的注册表
    booster_registry = {}

    def __init__(self):
        pass

    def auto_discovery(self):
        """
        通过扫描机制完成task函数的静态注册
        """

        # 在包中进行扫描注册
        def auto_register(mod):
            # 对类进行扫描
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if hasattr(method, 'queue_name') or hasattr(method, 'booster'):
                        queue_name = getattr(obj, 'queue_name', None)
                        booster = getattr(obj, 'booster', None)
                        self.booster_registry[queue_name] = {
                            'function': method,
                            'queue_name': queue_name,
                            'booster': booster
                        }
            # 对函数进行扫描
            for _, obj in inspect.getmembers(mod, inspect.isfunction):
                if hasattr(obj, 'queue_name') or hasattr(obj, 'booster'):
                    queue_name = getattr(obj, 'queue_name', None)
                    booster = getattr(obj, 'booster', None)
                    self.booster_registry[queue_name] = {
                        'function': obj,
                        'queue_name': queue_name,
                        'booster': booster
                    }

        # 自动确定项目根目录
        project_root = os.path.dirname(os.path.abspath(__file__))
        # 自动扫描每一个包
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    # 模块名
                    module_name = os.path.splitext(file)[0]
                    # 相对于project_root模块路径的相对路径
                    module_path = os.path.relpath(root, project_root).replace(os.sep, '.')
                    full_module_name = f"{module_path}.{module_name}" if module_path else module_name
                    # 得到module对象
                    module = importlib.import_module(full_module_name)
                    # 对module进行再次扫描
                    auto_register(module)

    def add_task(self, queue_name: str, func_kwargs: dict = None, priority_boost_params: PriorityBoostParams = None):
        """
        调用publish去向队列中添加需要启动的函数和参数，这里一个队列可以有不同的函数
        """
        # 从注册表中获取queue_name对应的函数
        booster = self.booster_registry[queue_name]['booster']
        # todo:这里就要根据配置进行核心代码的编写了
        pass

    def start_queue(self, queue_name: str):
        """
        启动当前节点对某个队列的消费
        """

    def add_and_start(self, func: typing.Callable, queue_name: str, booster_params: BoostParams):
        """
        向队列中添加任务并启动当前节点对该队列的消费
        """

    def start_queues(self, queue_name_list: typing.List[str] = None):
        """
        启动当前节点对指定的队列消费,不传入时则为对所有队列的消费
        """
        pass
