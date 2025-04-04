# Import libraries
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Import Routers
# from routers import workers
# from .routers import workers
from .routers import workers
from .utilities.blackboxInternalAPI import BlackBoxInternal

# Configure FastAPI
app: FastAPI = FastAPI()
app.include_router(workers.router)

# Request logging middleware
@app.middleware("http")
async def RequestLogging(req: Request, call_next):
        print("************")
        print(f"RQUEST MADE")
        print(f"BY: {req.headers.get('user-agent')}")
        print(f"TO: {req.url.path}")
        print(f"METHOD: {req.method}")
        print("************")
        response = await call_next(req)
        return response


# Initialise BlackBox internal client
internalClient = BlackBoxInternal()

# Define API
@app.get('/')
def root():
    blackboxRes = internalClient.test().json()
    # print(blackboxRes.text)
    return JSONResponse(content={
        'msg': 'hello world!',
        'response': blackboxRes
    })