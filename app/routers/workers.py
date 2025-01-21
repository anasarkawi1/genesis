import json
from fastapi import APIRouter, Depends, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import typing_extensions as typing
import logging

# from dependencies.workers import createWorker
from ..utilities.workersUtilities import WorkersUtility, workerParamsType, WorkerInfoDict, workerUtilsErrStrings, WorkerUtilsException

# Configuration
class params:
    mode: str
    tradingPair: str
    interval: str
    exchange: str
logger = logging.getLogger('uvicorn.error')

# Configuration
responses = {
    404: {
        'description': 'Not Found'
    }
}

workerUtils = WorkersUtility(
    maxProcs=1,
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

@router.get('/_info')
async def getWorkerInfoEndpoint():
    pass


# ADMINISTRATION ROUTE
@router.get('/get-all-workers')
async def getAllWorkersEndpoint():
    workers = workerUtils.getAllWorkers()
    responseBody = json.dumps(workers)
    return Response(content=responseBody    , status_code=200)

# ADMINISTRATION ROUTE
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

@router.post('/_create')
async def createWorkerEndpoint(params: createEndpointParams):
    # print(params.workerParams)
    # result = workerUtils.createWorker(
        # userId=params.userId,
        # clientId=params.clientId,
        # workerParams=params.workerParams)
    # print(result)
    return Response(status_code=200)


class deleteEndpointParams(BaseModel):
    workerId: str

@router.delete('/_delete')
async def deleteWorkerEndpoint(params: deleteEndpointParams):
    result = workerUtils.deleteWorker(
        workerId=params.workerId
    )

    if result['msg'] == 'NX_PROC':
        return Response(content=f'{params.workerId}', status_code=304)
    elif result['result'] == True:
        return Response(status_code=200)



# createEndpointErrorsLiteral = typing.Literal["INSTANCING_FAILED"]
# createInstanceErrString: dict[workerUtilsErrStrings, createEndpointErrorsLiteral] = {
#    "MAX_PROC_REACHED": "INSTANCING_FAILED"
# }

#
# Endpoint routines
#

def createInstanceRoutine(
        userId: str,
        clientId: str,
        workerParams: workerParamsType
) -> WorkerInfoDict:
    try:
        result = workerUtils.createWorker(
            userId=userId,
            clientId=clientId,
            workerParams=workerParams)
        return result["msg"]
    except WorkerUtilsException as err:
        raise err


# Error response model
class ErrorResponseModel(BaseModel):
    msg: workerUtilsErrStrings

# Altername responses
alternateResponse = {
    "createEndpoint": {
        500: { "model": ErrorResponseModel }
    }
}

class CreateEndpointParams(BaseModel):
    userId: str
    clientId: str
    workerParams: workerParamsType
class CreateEndpointResponse(BaseModel):
    attr: WorkerInfoDict

@router.post(
        '/create',
        response_model=CreateEndpointResponse,
        responses=alternateResponse['createEndpoint'])
async def createInstanceEndpoint(params: CreateEndpointParams):
    try:
        result = createInstanceRoutine(
            params.userId,
            params.clientId,
            params.workerParams)
        # Success, return instance attributes
        returnContent = { "attr": result }
        print(returnContent)
        return JSONResponse(
            status_code=200,
            content=returnContent)
    except WorkerUtilsException as err:
        returnContent = {
            "msg": err.responseMsg
        }
        return JSONResponse(
            status_code=err.responseStatusCode,
            content=returnContent)

# @router.get('/get-worker')
# 
# @router.delete('/delete')
# 
# @router.post('/set-algorithm')
# 
# @router.post('/unset-algorithm')
# 
# @router.post('/update-instance')

