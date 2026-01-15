from abc import ABC, abstractmethod

class Middleware(ABC):
    """
    Abstract base class for all middlewares.
    """
    @abstractmethod
    async def __call__(self, request, call_next):
        """
        :param request: The incoming request object.
        :param call_next: A callable that accepts the request and returns a response.
        :return: A Response object.
        """
        pass
