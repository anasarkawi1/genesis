import json
from uuid import uuid4
from .mercuryUtilities import createProcess
from pydantic import BaseModel
import os
from multiprocessing import Process
import signal
from threading import Lock


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


class WorkersUtility:

    def __init__(
            self,
            maxProcs,
            defaultWorkerPort
            ):
        
        # Runtime params
        self.maxProcs = maxProcs
        self.defaultWorkerPort = defaultWorkerPort
        self.currentPort = self.defaultWorkerPort
        self.procsList: dict[str, Process] = {}
        self.currentScanCursor = 0


    def createWorker(self, userId, workerParams: workerParamsType):
        if self.checkMaxProcNumber():
            return {
                'result': False,
                'msg': 'MAX_PROC_REACHED'
            }
        else:
            # There's enough space for a new instance. Proceed with thread instancing

            # Determine worker params
            global procKeyPrefix
            procKey = f'{procKeyPrefix}{str(uuid4())}'
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
                workerUserId    = userId
            )

            # Start the worker
            proc.start()
            self.procsList[procKey] = proc

            # Get worker process PID
            procPID = proc.pid
            
            workerInfo = {
                'PID': procPID,
                'port': procPort,
                'tradingPair': workerParams.tradingPair,
                'interval': workerParams.interval,
                'exchange': workerParams.exchange
            }

            return {
                'result': True,
                'msg': workerInfo
            }

    def getWorkers(self, userId):
        pass

    def deleteWorker(self, workerId):
        try:
            # Check if the process exists at all
            if not self.checkProcessExist(workerId=workerId):
                return {
                    'result': False,
                    'msg': 'NX_PROC'
                }

            # Kill the process
            # TODO: Well, this is equivalent to giving the finger to the process and the class instance. Maybe calling internal functions to terminate its operation is a better idea.
            self.procsList[workerId].terminate()

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
                proc.terminate()
            except Exception as e:
                raise e
        
        self.procsList.clear()
        
        return True