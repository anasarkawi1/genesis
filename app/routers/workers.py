from fastapi import APIRouter, Depends
# from dependencies.workers import createWorker

# Configuration
responses = {
    404: {
        'description': 'Not Found'
    }
}


# Declare API router
router = APIRouter(
    prefix='/workers',
    tags=['workers'],
    responses=responses
)


@router.get('/')
async def getWorkersEndpoint():
    return {
        "msg": "workers_test"
    }

@router.get('/info')
async def getWorkerInfoEndpoint():
    pass

@router.post('/create')
async def createWorkerEndpoint():
    pass