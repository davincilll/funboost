import abc
import asyncio
import contextvars
import logging
import threading
from dataclasses import dataclass

from funboost.core.function_result_status_saver import FunctionResultStatus


@dataclass
class FctContext:
    """
    fct 是 funboost current task 的简写
    """

    function_params: dict
    full_msg: dict
    function_result_status: FunctionResultStatus
    logger: logging.Logger
    asyncio_use_thread_concurrent_mode: bool = False


class _BaseCurrentTask(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def set_fct_context(self, fct_context: FctContext):
        raise NotImplemented

    @abc.abstractmethod
    def get_fct_context(self) -> FctContext:
        raise NotImplemented

    @property
    def function_params(self):
        return self.get_fct_context().function_params

    @property
    def full_msg(self) -> dict:
        return self.get_fct_context().full_msg

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self.get_fct_context().function_result_status

    @property
    def task_id(self) -> FunctionResultStatus:
        return self.function_result_status.task_id

    @property
    def logger(self) -> logging.Logger:
        return self.get_fct_context().logger

    def __str__(self):
        return f'<{self.__class__.__name__} [{self.function_result_status.get_status_dict()}]>'


class __ThreadCurrentTask(_BaseCurrentTask):
    """
    用于在用户自己函数内部去获取 消息的完整体,当前重试次数等.
    """

    _fct_local_data = threading.local()

    def set_fct_context(self, fct_context: FctContext):
        self._fct_local_data.fct_context = fct_context

    def get_fct_context(self) -> FctContext:
        return self._fct_local_data.fct_context


class __AsyncioCurrentTask(_BaseCurrentTask):
    _fct_context = contextvars.ContextVar('fct_context')

    def set_fct_context(self, fct_context: FctContext):
        self._fct_context.set(fct_context)

    def get_fct_context(self) -> FctContext:
        return self._fct_context.get()


thread_current_task = __ThreadCurrentTask()
asyncio_current_task = __AsyncioCurrentTask()


def is_asyncio_environment():
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def funboost_current_task():
    if is_asyncio_environment():
        if hasattr(thread_current_task._fct_local_data, 'fct_context') and thread_current_task.get_fct_context().asyncio_use_thread_concurrent_mode is True:
            # 如果用户使用的是默认的ConcurrentModeEnum.THREADING并发模式来运行async def 函数，那么也使用线程获取上下文
            return thread_current_task
        else:
            return asyncio_current_task
    else:
        return thread_current_task


def get_current_taskid():
    # return fct.function_result_status.task_id
    try:
        fct = funboost_current_task()
        return fct.task_id  # 不在funboost的消费函数里面或者同个线程、协程就获取不到上下文了
    except (AttributeError, LookupError) as e:
        # print(e,type(e))
        return 'no_task_id'


class FctContextThread(threading.Thread):
    """
    这个类自动把当前线程的 线程上下文 自动传递给新开的线程。
    """

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None,
                 ):
        threading.Thread.__init__(**locals())
        self.fct_context = thread_current_task.get_fct_context()

    def run(self):
        thread_current_task.set_fct_context(self.fct_context)
        super().run()


if __name__ == '__main__':
    print(is_asyncio_environment())
    print()
    for i in range(2):
        funboost_current_task()
        print(get_current_taskid())
    print()
