# Import libraries
from fastapi import FastAPI, Request

# Import Routers
# from routers import workers
# from .routers import workers
from .routers import workers

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

# Define API
@app.get('/')
def root():
    return {
        'msg': 'hello world!'
    }