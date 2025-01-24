import json
from fastapi import APIRouter, Response, Request
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
    supervisorPort=8070,
    logger=logger)


# Declare API router
router = APIRouter(
    prefix='/clients',
    tags=['clients'],
    responses=responses)


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



#
# Error and alternate responses definitions
#

# Error response model
class ErrorResponseModel(BaseModel):
    msg: workerUtilsErrStrings

class ClientNotFoundResponseModel(ErrorResponseModel):
    msg: workerUtilsErrStrings = "CLIENT_NOT_FOUND"

# TODO: Define common alternates
alternateResponse = {
    "createEndpoint": {
        500: { "model": ErrorResponseModel }
    },
    "getClientInfoEndpoint": {
        500: { "model": ErrorResponseModel },
        400: { "model": ClientNotFoundResponseModel },
    },
    "setAlgorithmEndpoint": {
        400: { "model": ClientNotFoundResponseModel }
    }
}


#
# Create Client Endpoint
#

class CreateEndpointParams(BaseModel):
    userId: str
    clientId: str
    workerParams: workerParamsType
class CreateEndpointResponse(BaseModel):
    attr: WorkerInfoDict

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

@router.put(
        '/',
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


#
# Get Client Info Endpoint
#

class ClientInfoRequestBodyModel(BaseModel):
    client_id: str

class ClientInfoResponseModel(BaseModel):
    proc_pid        : str
    proc_port       : int
    tradingPair     : str
    interval        : str
    exchange        : str

def getClientInfo(
    clientId: str
) -> ClientInfoResponseModel:
    try:
        result = workerUtils.getClientInfo(clientId)
        output = {
            "proc_pid"              : result["PID"],
            "proc_port"             : result["port"],
            "tradingPair"           : result["tradingPair"],
            "interval"              : result["interval"],
            "exchange"              : result["exchange"],
            "algorithmId"           : result["algorithmId"],
        }
        return output
    except WorkerUtilsException as err:
        raise err

@router.get(
        '/',
        response_model=ClientInfoResponseModel,
        responses=alternateResponse['getClientInfoEndpoint'])
async def getClientInfoEndpoint(body: ClientInfoRequestBodyModel):
    try:
        # Success, return instance attributes
        result = getClientInfo(body.client_id)
        returnContent = { "attr": result }
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


#
# Delete client endpoint
#

class DeleteClientRequestBody(BaseModel):
    client_id: str

@router.delete('/')
async def deleteClientEndpoint(params: DeleteClientRequestBody):
    try:
        result = workerUtils.deleteWorker(workerId=params.client_id)
        returnContent = {
            "msg": result["msg"]
        }
        return JSONResponse(
            status_code=200,
            content=returnContent
        )
    except WorkerUtilsException as err:
        returnContent = {
            "msg": err.responseMsg
        }
        return JSONResponse(
            status_code=err.responseStatusCode,
            content=returnContent)


#
# Set Algorithm Endpoint
#

class SetAlgorithmRequestBody(BaseModel):
    client_id           : str
    algorithm_id        : str
    algorithm           : dict

def setAlgorithm(clientId, algorithmId, algorithm):
    try:
        result = workerUtils.setClientAlgorithm(clientId, algorithmId, algorithm)
        # logger.info(result)
        return result
    except WorkerUtilsException as err:
        raise err

@router.post('/set-algorithm')
async def setAlgorithmEndpoint(params: SetAlgorithmRequestBody):
    try:
        res = setAlgorithm(
            params.client_id,
            params.algorithm_id,
            params.algorithm,
        )
        return res
    except WorkerUtilsException as err:
        returnContent = {
            "msg": err.responseMsg
        }
        return JSONResponse(
            status_code=err.responseStatusCode,
            content=returnContent)


# @router.post('/unset-algorithm')
#
# @router.post('/update-instance')
