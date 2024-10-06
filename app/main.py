# Import libraries
from fastapi import FastAPI

# Import Routers
from app.routers import workers


# Configure FastAPI
app: FastAPI = FastAPI()
app.include_router(workers.router)

# Define API
@app.get('/')
async def root():
    return {
        'msg': 'hello world!'
    }