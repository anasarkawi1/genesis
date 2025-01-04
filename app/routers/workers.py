import json
from fastapi import APIRouter, Depends, Response, Request
from pydantic import BaseModel

# from dependencies.workers import createWorker
from ..utilities.workersUtilities import WorkersUtility, workerParamsType

# Configuration
class params:
    mode: str
    tradingPair: str
    interval: str
    exchange: str


# Configuration
responses = {
    404: {
        'description': 'Not Found'
    }
}

workerUtils = WorkersUtility(
    maxProcs=10,
    defaultWorkerPort=8071,
    supervisorPort=8070
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

@router.get('/get-all-workers')
async def getAllWorkersEndpoint():
    workers = workerUtils.getAllWorkers()
    responseBody = json.dumps(workers)
    return Response(content=responseBody    , status_code=200)

@router.delete('/reset-state')
async def resetState(request: Request):
    # workerUtils.killAllClientsAndRecords()
    clientIp = request.client.host
    if clientIp == '127.0.0.1':
        workerUtils.killAllClientsAndRecords()
        return Response(status_code=204)
    else:
        return Response(status_code=403)

# TODO: Define a Dataparams thing for the req body fields
#       use that for creating processes.


class createEndpointParams(BaseModel):
    userId: str
    clientId: str
    workerParams: workerParamsType

@router.post('/create')
async def createWorkerEndpoint(params: createEndpointParams):
    # print(params.workerParams)
    result = workerUtils.createWorker(
        userId=params.userId,
        clientId=params.clientId,
        workerParams=params.workerParams)
    # print(result)
    return Response(status_code=200)


class deleteEndpointParams(BaseModel):
    workerId: str

@router.delete('/delete')
async def deleteWorkerEndpoint(params: deleteEndpointParams):
    result = workerUtils.deleteWorker(
        workerId=params.workerId
    )

    if result['msg'] == 'NX_PROC':
        return Response(content=f'{params.workerId}', status_code=304)
    elif result['result'] == True:
        return Response(status_code=200)