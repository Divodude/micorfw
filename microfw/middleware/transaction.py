from microfw.middleware.base import Middleware

class TransactionMiddleware(Middleware):
    async def __call__(self, request, call_next):
        try:
            response = await call_next(request)
            if hasattr(request, 'db') and request.db:
                await request.db.commit()
            return response
        except Exception:
            if hasattr(request, 'db') and request.db:
                await request.db.rollback()
            raise
