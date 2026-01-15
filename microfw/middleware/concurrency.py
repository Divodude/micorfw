import asyncio
from microfw.response import Response
from microfw.settings import settings

class ConcurrencyMiddleware:
    def __init__(self, limit: int = None, max_wait: float = None):
        self.limit = limit or settings.CONCURRENCY_LIMIT
        self.max_wait = max_wait or settings.CONCURRENCY_MAX_WAIT
        self.semaphore = asyncio.Semaphore(self.limit)

    async def __call__(self, request, call_next):
        try:
            # Try to acquire semaphore with timeout
            async with asyncio.timeout(self.max_wait):
                await self.semaphore.acquire()
        except TimeoutError:
             return Response("503 Service Unavailable: Queue Full", status_code=503, headers={"Retry-After": "1"})
        except Exception:
       
             return Response("503 Service Unavailable", status_code=503)
        
        try:
            return await call_next(request)
        finally:
            self.semaphore.release()
