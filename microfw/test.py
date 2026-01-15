from app import App
from request import Request
from response import Response





app=App()

@app.route("/",methods=["GET"])
def index():
    return Response("Hello World",status_code=200,headers={"Content-Type":"text/plain"})

if __name__=="__main__":
    print(app.dispatch(Request("/","GET")))