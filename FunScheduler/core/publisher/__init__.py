import abc


class PublishParams:
    pass


class AbstractPublisher(metaclass=abc.ABCMeta):
    publish_params: PublishParams

    @abc.abstractmethod
    def publish(self, publish_params: PublishParams):
        raise NotImplementedError
