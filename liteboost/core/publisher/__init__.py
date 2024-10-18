import abc
import typing


class PublishParams:
    pass


class BasePublisher(metaclass=abc.ABCMeta):
    publish_params: PublishParams


    def publish(self, publish_params: PublishParams):
        raise NotImplementedError

    @abc.abstractmethod
    def _publish(self, msg: typing.Union[str, dict]):
        raise NotImplementedError


class AbstractPublisher(LoggerLevelSetterMixin, metaclass=abc.ABCMeta, ):
    def __init__(self, publisher_params: PublisherParams, ):
        self.publisher_params = publisher_params
        self.queue_name = self._queue_name = publisher_params.queue_name
        self.logger: logging.Logger
        self._build_logger()
        self.publish_params_checker = PublishParamsChecker(publisher_params.consuming_function) if publisher_params.consuming_function else None

        self.has_init_broker = 0
        self._lock_for_count = Lock()
        self._current_time = None
        self.count_per_minute = None
        self._init_count()
        self.custom_init()
        self.logger.info(f'{self.__class__} 被实例化了')
        self.publish_msg_num_total = 0

        self.__init_time = time.time()
        atexit.register(self._at_exit)
        if publisher_params.clear_queue_within_init:
            self.clear()

    def _build_logger(self):
        logger_prefix = self.publisher_params.logger_prefix
        if logger_prefix != '':
            logger_prefix += '--'
        self.logger_name = self.publisher_params.logger_name or f'funboost.{logger_prefix}{self.__class__.__name__}--{self.queue_name}'
        self.log_filename = self.publisher_params.log_filename or f'funboost.{self.queue_name}.log'
        self.logger = nb_log.LogManager(self.logger_name, logger_cls=TaskIdLogger).get_logger_and_add_handlers(
            log_level_int=self.publisher_params.log_level,
            log_filename=self.log_filename if self.publisher_params.create_logger_file else None,
            error_log_filename=nb_log.generate_error_file_name(self.log_filename),
            formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER, )

    def _init_count(self):
        self._current_time = time.time()
        self.count_per_minute = 0

    def custom_init(self):
        pass

    @staticmethod
    def _get_from_other_extra_params(k: str, msg):
        # msg_dict = json.loads(msg) if isinstance(msg, str) else msg
        msg_dict = Serialization.to_dict(msg)
        return msg_dict['extra'].get('other_extra_params', {}).get(k, None)

    def _convert_msg(self, msg: typing.Union[str, dict], task_id=None,
                     priority_control_config: PriorityConsumingControlConfig = None) -> (typing.Dict, typing.Dict, typing.Dict, str):
        msg = Serialization.to_dict(msg)
        msg_function_kw = copy.deepcopy(msg)
        raw_extra = {}
        if 'extra' in msg:
            msg_function_kw.pop('extra')
            raw_extra = msg['extra']
        if self.publish_params_checker and self.publisher_params.should_check_publish_func_params:
            self.publish_params_checker.check_params(msg_function_kw)
        task_id = task_id or MsgGenerater.generate_task_id(self._queue_name)
        extra_params = MsgGenerater.generate_pulish_time_and_task_id(self._queue_name, task_id=task_id)
        if priority_control_config:
            extra_params.update(priority_control_config.dict(exclude_none=True))
        extra_params.update(raw_extra)
        msg['extra'] = extra_params
        return msg, msg_function_kw, extra_params, task_id

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None):
        """

        :param msg:函数的入参字典或者字典转json。,例如消费函数是 def add(x,y)，你就发布 {"x":1,"y":2}
        :param task_id:可以指定task_id,也可以不指定就随机生产uuid
        :param priority_control_config:优先级配置，消息可以携带优先级配置，覆盖boost的配置。
        :return:
        """
        msg = copy.deepcopy(msg)  # 字典是可变对象,不要改变影响用户自身的传参字典. 用户可能继续使用这个传参字典.
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        # 这里调用具体实现类的publish方法
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self.concrete_realization_of_publish)(Serialization.to_json_str(msg))

        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}', extra={'task_id': task_id})  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        return AsyncResult(task_id)

    def send_msg(self, msg: typing.Union[dict, str]):
        """直接发送任意消息内容到消息队列,不生成辅助参数,无视函数入参名字,不校验入参个数和键名"""
        decorators.handle_exception(retry_times=10, is_throw_error=True, time_sleep=0.1)(
            self.concrete_realization_of_publish)(Serialization.to_json_str(msg))

    @staticmethod
    def __get_cls_file(cls: type):
        if cls.__module__ == '__main__':
            cls_file = Path(sys.argv[0]).resolve().as_posix()
        else:
            cls_file = Path(sys.modules[cls.__module__].__file__).resolve().as_posix()
        return cls_file

    def push(self, *func_args, **func_kwargs):
        """
        简写，只支持传递消费函数的本身参数，不支持priority_control_config参数。
        类似于 publish和push的关系类似 apply_async 和 delay的关系。前者更强大，后者更简略。

        例如消费函数是
        def add(x,y):
            print(x+y)

        publish({"x":1,'y':2}) 和 push(1,2)是等效的。但前者可以传递priority_control_config参数。后者只能穿add函数所接受的入参。
        :param func_args:
        :param func_kwargs:
        :return:
        """
        # print(func_args, default_kwargs, self.publish_params_checker.all_arg_name)
        msg_dict = func_kwargs
        # print(msg_dict)
        # print(self.publish_params_checker.position_arg_name_list)
        # print(func_args)
        func_args_list = list(func_args)
        if self.publisher_params.consuming_function_kind == FunctionKind.CLASS_METHOD:
            # print(self.publish_params_checker.all_arg_name[0])
            # func_args_list.insert(0, {'first_param_name': self.publish_params_checker.all_arg_name[0],
            #        'cls_type': ClsHelper.get_classs_method_cls(self.publisher_params.consuming_function).__name__},
            #                       )
            cls = func_args_list[0]
            # print(cls,cls.__name__, sys.modules[cls.__module__].__file__)

            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 }
        elif self.publisher_params.consuming_function_kind == FunctionKind.INSTANCE_METHOD:
            obj = func_args[0]
            cls = type(obj)
            if not hasattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS):
                raise ValueError(f'消费函数 {self.publisher_params.consuming_function} 是实例方法，实例必须有 {ConstStrForClassMethod.OBJ_INIT_PARAMS} 属性')
            func_args_list[0] = {ConstStrForClassMethod.FIRST_PARAM_NAME: self.publish_params_checker.all_arg_name[0],
                                 ConstStrForClassMethod.CLS_NAME: cls.__name__,
                                 ConstStrForClassMethod.CLS_FILE: self.__get_cls_file(cls),
                                 ConstStrForClassMethod.CLS_MODULE: PathHelper(self.__get_cls_file(cls)).get_module_name(),
                                 ConstStrForClassMethod.OBJ_INIT_PARAMS: getattr(obj, ConstStrForClassMethod.OBJ_INIT_PARAMS),

                                 }

        for index, arg in enumerate(func_args_list):
            # print(index,arg,self.publish_params_checker.position_arg_name_list)
            # msg_dict[self.publish_params_checker.position_arg_name_list[index]] = arg
            msg_dict[self.publish_params_checker.all_arg_name[index]] = arg

        # print(msg_dict)
        return self.publish(msg_dict)

    delay = push  # 那就来个别名吧，两者都可以。

    @abc.abstractmethod
    def concrete_realization_of_publish(self, msg: str):
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_message_count(self):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self.logger.warning(f'with中自动关闭publisher连接，累计推送了 {self.publish_msg_num_total} 条消息 ')

    def _at_exit(self):
        if multiprocessing.current_process().name == 'MainProcess':
            self.logger.warning(
                f'程序关闭前，{round(time.time() - self.__init_time)} 秒内，累计推送了 {self.publish_msg_num_total} 条消息 到 {self._queue_name} 中')
