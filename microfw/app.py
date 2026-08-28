from microfw.exceptions import HTTPException
from microfw.response import Response
try:
    from microfw.serializers import BaseModel, ValidationError
except ImportError:
    BaseModel = None
    ValidationError = None

import re
from microfw.service_registry import ServiceRegistry
from microfw.middleware.context import ContextMiddleware
from microfw.settings import settings

from microfw.router import RadixRouter

class App:
    def __init__(self):
        self.router = RadixRouter()
        self.middlewares = []
        self.startup_handlers = []
        self.shutdown_handlers = []
        self.services = ServiceRegistry()
        # Add ContextMiddleware as the VERY FIRST middleware so it runs first
        self.middlewares.append(ContextMiddleware(self.services, service_name=settings.SERVICE_NAME))

    def on_event(self, event_type):
        def wrapper(func):
            if event_type == "startup":
                self.startup_handlers.append(func)
            elif event_type == "shutdown":
                self.shutdown_handlers.append(func)
            return func
        return wrapper

    def add_service(self, name: str, base_url: str):
        self.services.register(name, base_url)

    def route(self, path, methods=["GET"], middlewares=None):
        def wrapper(func):
            for method in methods:
                self.router.add_route(
                    method=method,
                    path=path,
                    handler_info={
                        "handler": func,
                        "middlewares": middlewares or [],
                        "compiled_handler": None # Will be lazily compiled on first request
                    }
                )
            return func
        return wrapper

    def middleware(self, func):
        self.middlewares.append(func)
        return func



    async def dispatch(self, request):
        handler_info, kwargs = self.router.match_route(request.method, request.path)
        
        if not handler_info:
            # 404 Handler
            class NotFoundResponse:
                status_code = 404
                headers = {}
                data = "404 Not Found"
            return NotFoundResponse()

        # Compile middleware chain lazily and cache it
        if handler_info["compiled_handler"] is None:
            handler_func = handler_info["handler"]
            route_middlewares = handler_info["middlewares"]
            
            import inspect
            sig = inspect.signature(handler_func)

            async def base_handler(req, route_kwargs):
                pass_args = {}
                
                # --- Pydantic Injection Logic ---
                if BaseModel:
                    for name, param in sig.parameters.items():
                        if isinstance(param.annotation, type) and issubclass(param.annotation, BaseModel):
                            try:
                                body_data = await req.json()
                                model_instance = param.annotation(**body_data)
                                pass_args[name] = model_instance
                            except ValidationError as e:
                                return Response(data={"error": e.errors()}, status_code=422, headers={"Content-Type": "application/json"})
                            except Exception as e:
                                 return Response(data={"error": "Invalid JSON body"}, status_code=400)
                # --------------------------------

                if len(sig.parameters) > 0:
                    if 'request' in sig.parameters:
                        pass_args['request'] = req
                    
                    for name, value in route_kwargs.items():
                        if name in sig.parameters:
                            pass_args[name] = value

                if inspect.iscoroutinefunction(handler_func):
                    result = await handler_func(**pass_args)
                else:
                    result = handler_func(**pass_args)
                
                # --- Pydantic Response Logic ---
                if BaseModel and isinstance(result, BaseModel):
                     return Response(data=result.model_dump(), status_code=200, headers={"Content-Type": "application/json"})
                
                if isinstance(result, dict) or isinstance(result, list):
                     return Response(data=result)
                
                return result

            # Build Chain
            all_middlewares = self.middlewares + route_middlewares
            
            # Since base_handler needs route_kwargs, and the middleware chain expects `req` only,
            # we must build a factory that takes `route_kwargs` and returns the fully wrapped chain for that request,
            # OR we pass `route_kwargs` down the chain?
            # Standard middlewares expect (request, call_next).
            # So `call_next(req)` -> calls next middleware, eventually calling `base_handler(req, route_kwargs)`
            
            # Since route_kwargs change per request, the compiled chain itself can't hardcode them.
            # But the closures can accept route_kwargs.
            
            def build_chain(route_kwargs):
                async def closure_base(req):
                    return await base_handler(req, route_kwargs)
                
                handler = closure_base
                for m in reversed(all_middlewares):
                    # Default argument binding trick for closures in loop
                    def wrap(middleware, next_handler):
                        async def wrapped(req):
                            result = middleware(req, next_handler)
                            if inspect.isawaitable(result):
                                return await result
                            return result
                        return wrapped
                    handler = wrap(m, handler)
                return handler
                
            handler_info["compiled_handler"] = build_chain

        # Execute with Error Handling
        try:
            # Generate the request-specific handler chain using the cached factory
            chain = handler_info["compiled_handler"](kwargs)
            return await chain(request)
        except HTTPException as e:
            return Response(data=e.detail, status_code=e.status_code, headers=e.headers)
        except Exception as e:
            print(f"Internal Server Error: {e}")
            import traceback
            traceback.print_exc()
            return Response(data="Internal Server Error", status_code=500)
