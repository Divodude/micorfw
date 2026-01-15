import asyncio
from microfw.request import Request

class ASGI:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    # Run startup handlers
                    try:
                        for handler in self.app.startup_handlers:
                             if asyncio.iscoroutinefunction(handler):
                                 await handler()
                             else:
                                 handler()
                        await send({"type": "lifespan.startup.complete"})
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        await send({"type": "lifespan.startup.failed", "message": str(e)})
                        return
                elif message["type"] == "lifespan.shutdown":
                    # Run shutdown handlers
                    try:
                        for handler in self.app.shutdown_handlers:
                             if asyncio.iscoroutinefunction(handler):
                                 await handler()
                             else:
                                 handler()
                        await send({"type": "lifespan.shutdown.complete"})
                        return
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        await send({"type": "lifespan.shutdown.failed", "message": str(e)})
                        return
        elif scope["type"] == "http":
            await self._handle_http(scope, receive, send)

    async def _handle_http(self, scope, receive, send):
        event = await receive()

        body = event.get("body", b"")

        request = Request(
            method=scope["method"],
            path=scope["path"],
            query=scope["query_string"].decode(),
            header={k.decode(): v.decode() for k, v in scope["headers"]},
            body=body
        )

        response = await self.app.dispatch(request)

        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                (k.encode(), v.encode())
                for k, v in response.headers.items()
            ],
        })

        await send({
            "type": "http.response.body",
            "body": str(response.data).encode(),
        })
