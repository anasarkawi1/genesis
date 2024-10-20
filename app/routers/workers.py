from fastapi import APIRouter, Depends
# from dependencies.workers import createWorker
from ..utilities.workersUtilities import WorkersUtility

# Configuration
responses = {
    404: {
        'description': 'Not Found'
    }
}
redisParams = {
    'host': '192.168.1.5',
    'port': 6379
}

workerUtils = WorkersUtility(
    maxProcs=10,
    redisParams=redisParams,
    defaultWorkerPort=8071
)


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