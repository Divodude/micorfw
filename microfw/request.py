import json

class Request:
    def __init__(self,path,method,query=None,header=None,body=None):
        self.path=path
        self.method=method.upper()
        self.query=query or {}
        self.header=header or {}
        self.body=body
        self.body=body
        self.db=None
        self.context=None # type: microfw.context.RequestContext
        self.client=None # type: microfw.client.ServiceClient

    async def json(self):
        if not self.body:
            return {}
        return json.loads(self.body)
    