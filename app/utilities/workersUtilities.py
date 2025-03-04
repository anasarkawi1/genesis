import json
from uuid import uuid4
from .mercuryUtilities import createProcess
from pydantic import BaseModel
import os
from multiprocessing import Process, active_children
import signal
from threading import Lock
import typing_extensions as typing
import requests
from .localClientAPI import LocalClient
from sys import stdout


#
# Configuration
#
procKeyPrefixProd = f'mercuryGenesis-clientId-'
procKeyPrefix = f'client-'

class workerParamsType(BaseModel):
    mode: str
    tradingPair: str
    interval: str
    exchange: str

#
# Error definitions
#

# Possible error response values
workerUtilsErrStrings = typing.Literal[
    "MAX_SYSTEM_PROCS_REACHED",
    "CLIENT_NOT_FOUND",
    "ALGORITHM_SET_FAILED",
    "ALGORITHM_UNSET_FAILED"]
# Base error class
class WorkerUtilsException(Exception):
    errCode                 : int
    responseMsg             : workerUtilsErrStrings
    responseStatusCode      : int

# Available system processes limit reached
class MaxProcsException(WorkerUtilsException):
    errCode                 = 1001
    responseMsg             = "MAX_SYSTEM_PROCS_REACHED"
    responseStatusCode      = 500

# Client not found exception
class ClientNotFoundException(WorkerUtilsException):
    errCode                 = 1002
    responseMsg             = "CLIENT_NOT_FOUND"
    responseStatusCode      = 400

# Algorithm setting failed
class AlgorithmSetFailedException(WorkerUtilsException):
    errCode                 = 1003
    responseMsg             = "ALGORITHM_SET_FAILED"
    responseStatusCode      = 500

class AlgorithmUnsetFailedException(WorkerUtilsException):
    errCode                 = 1004
    responseMsg             = "ALGORITHM_UNSET_FAILED"
    responseStatusCode      = 500

class WorkerInfoDict(typing.TypedDict):
        PID             : str
        port            : str
        tradingPair     : str
        interval        : str
        exchange        : str
        algorithmId     : str | None
class createWorkerReturn(typing.TypedDict):
    result: bool
    msg: WorkerInfoDict | None
    err: workerUtilsErrStrings | None

class WorkersUtility:

    def __init__(
            self,
            maxProcs,
            defaultWorkerPort,
            supervisorPort,
            logger
            ):
        
        # Runtime params
        self.maxProcs = maxProcs
        self.defaultWorkerPort = defaultWorkerPort
        self.currentPort = self.defaultWorkerPort
        self.procsList: dict[str, list[Process, dict[str, any]]] = {}
        self.currentScanCursor = 0
        # Used for updating
        self.supervisorPort = supervisorPort
        self.logger = logger

        # Client API
        self.client = LocalClient()

    def createWorker(
            self,
            userId,
            clientId,
            workerParams: workerParamsType) -> createWorkerReturn:
        if self.checkMaxProcNumber():
            raise MaxProcsException
        else:
            # There's enough space for a new instance. Proceed with thread instancing

            # Determine worker params
            global procKeyPrefix
            procKey = f'{clientId}'
            procPort = self.getCurrentPort()

            # Get API credentials
            key, secret = self.getCreds(userId)

            # Create worker instance
            proc = createProcess(
                apiKey          = key,
                apiSecret       = secret,
                mode            = workerParams.mode,
                tradingPair     = workerParams.tradingPair,
                interval        = workerParams.interval,
                exchange        = workerParams.exchange,
                workerId        = procKey,
                workerPort      = procPort,
                workerName      = '',
                workerUserId    = userId,
                supervisorPort  = self.supervisorPort,
                logger          = self.logger
            )

            # Start the worker
            proc.start()
            # Get worker process PID
            procPID = proc.pid

            # workerInfo = {
                # 'PID': procPID,
                # 'port': procPort,
                # 'tradingPair': workerParams.tradingPair,
                # 'interval': workerParams.interval,
                # 'exchange': workerParams.exchange
            # }
            workerInfo: WorkerInfoDict = {
                'PID'           : procPID,
                'port'          : procPort,
                'tradingPair'   : workerParams.tradingPair,
                'interval'      : workerParams.interval,
                'exchange'      : workerParams.exchange,
                'algorithmId'   : None
            }

            
            self.procsList[procKey] = [
                proc,
                workerInfo
            ]

            return {
                'result': True,
                'msg': workerInfo
            }

    # def getWorkers(self, userId):
    #     pass
    def getClientInfo(self, clientId):
        try:
            client = self.procsList[clientId]
            return client[1]
        except KeyError:
            raise ClientNotFoundException

    def getAllWorkers(self):
        output = {}
        for key, proc in self.procsList.items():
            output[key] = proc[1]
        return output

    def deleteWorker(self, workerId):
        try:
            # Check if the process exists at all
            procExists = self.checkProcessExist(workerId=workerId)
            if not procExists:
                raise ClientNotFoundException
                # return {
                #     'result': False,
                #     'msg': 'NX_PROC'
                # }

            # Kill the process
            # TODO: Well, this is equivalent to giving the finger to the process and the class instance. Maybe calling internal functions to terminate its operation is a better idea.
            self.procsList[workerId][0].terminate()

            # Delete the key from the dict
            del self.procsList[workerId]

        except Exception as e:
            raise e
        
        return {
            'result': True,
            'msg': 'WORKER_DELETED_SUCCESS'
        }
    
    def setClientAlgorithm(self, clientId, algorithmId, algorithm, entryCost):
        try:
            clientPort = self.getClientPort(clientId=clientId)
            reqBody = {
                "algorithm_id"    : algorithmId,
                "algorithm"       : algorithm,
                "entry_cost"      : entryCost
            }
            res = self.client.setAlgorithm(port=clientPort, data=reqBody)
            # Check if the request was successful
            if res.status_code == 200:
                self.procsList[clientId][1]['algorithmId'] = algorithmId
                return res.json()
            # Algorithm set failed, raise error
            else:
                # print(f"Status code is non 200!! Code: {res.status_code}. Response Body:")
                # print(res.json())
                stdout.flush()
                raise AlgorithmSetFailedException
            # 
            # res = self.client.getInfo(port=clientPort)
            # return res.json()
        except WorkerUtilsException as err:
            raise err
    
    def unsetClientAlgorithm(self, clientId):
        try:
            clientPort = self.getClientPort(clientId=clientId)
            res = self.client.unsetAlgorithm(port=clientPort)
            print(res)
            stdout.flush()
            return res.json()
            if res.status_code == 200:
                self.procsList[clientId][1]['algorithmId'] = None
            else:
                # raise AlgorithmUnsetFailedException
                pass
        except WorkerUtilsException as err:
            raise err


    # Utils
    def getCreds(self, userId):
        # Hardcoded for now...
        apiKey = os.getenv("API_KEY")
        apiSecret = os.getenv("API_SECRET")
        return [apiKey, apiSecret]

    def getCurrentPort(self):
        returnPort = self.currentPort
        self.currentPort += 1
        return returnPort
        
    def checkMaxProcNumber(self):
        currentProcNumber = len(self.procsList)
        return True if (currentProcNumber >= self.maxProcs) else False
    
    def getClientPort(self, clientId):
        try:
            clientAttr = self.procsList[clientId]
            return clientAttr[1]["port"]
        except KeyError:
            raise ClientNotFoundException
    
    def checkProcessExist(self, workerId):
        return True if (workerId in self.procsList) else False
    
    # Kills and purges all processes, whether they exist or not. Used for system system resets.
    def killAllClientsAndRecords(self):
        # Itirate through the list of processes and terminate them
        for key, proc in self.procsList.items():
            try:
                proc[0].terminate()
            except Exception as e:
                raise e
        
        self.procsList.clear()
        
        return True