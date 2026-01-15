import json

class Response:
    def __init__(self, data, status_code=200, headers=None):
        self.headers = headers or {}
        self.status_code = status_code
        
        if isinstance(data, (dict, list)):
            self.data = json.dumps(data)
            self.headers["Content-Type"] = "application/json"
        else:
            self.data = data
            if "Content-Type" not in self.headers:
                 self.headers["Content-Type"] = "text/plain"

    def __str__(self):
        return self.data