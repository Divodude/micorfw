from microfw.orm_db import Database

class DatabaseMiddleware:
    def __init__(self, db: Database):
        self.db = db

    async def __call__(self, request, call_next):
        async with await self.db.session() as session:
            request.db = session
            try:
                response = await call_next(request)
                return response
            except Exception:
                raise
            finally:
                # AsyncSession context manager handles close/rollback usually,
                # but explicit close ensures cleanliness if session factory behavior varies.
                # However, async with does it. 
                pass
