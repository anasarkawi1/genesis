import json
from uuid import uuid4
from .mercuryUtilities import createProcess
from pydantic import BaseModel
import os
from multiprocessing import Process
import signal
from threading import Lock
import typing_extensions as typing


#
# Configuration
#
procKeyPrefixProd = f'mercuryGenesis-clientId-'
procKeyPrefix = f'client-'

workerUtilsErrStrings = typing.Literal["MAX_SYSTEM_PROCS_REACHED"]

class WorkerUtilsException(Exception):
    errCode                 : int
    responseMsg             : workerUtilsErrStrings
    responseStatusCode      : int

class MaxProcsException(WorkerUtilsException):
    errCode                 = 1001
    responseMsg             = "MAX_SYSTEM_PROCS_REACHED"
    responseStatusCode      = 500

class workerParamsType(BaseModel):
    mode: str
    tradingPair: str
    interval: str
    exchange: str


class WorkerInfoDict(typing.TypedDict):
        PID             : str
        port            : str
        tradingPair     : str
        interval        : str
        exchange        : str
class createWorkerReturn(typing.TypedDict):
    result: bool
    msg: WorkerInfoDict | None
    err: workerUtilsErrStrings | None

class WorkersUtility:

    def __init__(
            self,
            maxProcs,
            defaultWorkerPort,
            supervisorPort
            ):
        
        # Runtime params
        self.maxProcs = maxProcs
        self.defaultWorkerPort = defaultWorkerPort
        self.currentPort = self.defaultWorkerPort
        self.procsList: dict[str, list(Process, dict[str, any])] = {}
        self.currentScanCursor = 0
        # Used for updating
        self.supervisorPort = supervisorPort

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
                supervisorPort  = self.supervisorPort
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
                'PID':              procPID,
                'port':             procPort,
                'tradingPair':      workerParams.tradingPair,
                'interval':         workerParams.interval,
                'exchange':         workerParams.exchange
            }

            
            self.procsList[procKey] = [
                proc,
                workerInfo
            ]

            return {
                'result': True,
                'msg': workerInfo
            }

    def getWorkers(self, userId):
        pass

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
                return {
                    'result': False,
                    'msg': 'NX_PROC'
                }

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