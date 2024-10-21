# Import libraries
from fastapi import FastAPI

# Import Routers
# from routers import workers
# from .routers import workers
from .routers import workers

# Configure FastAPI
app: FastAPI = FastAPI()
app.include_router(workers.router)

# Define API
@app.get('/')
def root():
    return {
        'msg': 'hello world!'
    }