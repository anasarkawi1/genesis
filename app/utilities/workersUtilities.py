from redis import Redis
import json
from uuid import uuid4
from .mercuryUtilities import createProcess
from pydantic import BaseModel
import os
from multiprocessing import Process
import signal


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
            redisParams,
            defaultWorkerPort
            ):

        # Redis Client
        self.redisClient = Redis(
            host=redisParams['host'],
            port=redisParams['port'],
            decode_responses=True)
        self.redisKeys = {
            'procsKeys': 'procsList',
            'currentPort': 'procsCurrentPort'
        }
        
        # Runtime params
        self.maxProcs = maxProcs
        self.defaultWorkerPort = defaultWorkerPort
        self.procsList: dict[str, Process] = {}
        self.currentScanCursor = 0

        # Reset all clients and reset the whole system to a default state
        # TODO: Implement above...


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

            # Write worker info into redis
            workerInfo = {
                'PID': procPID,
                'port': procPort,
                'tradingPair': workerParams.tradingPair,
                'interval': workerParams.interval,
                'exchange': workerParams.exchange
            }
            redisWriteResult = self.redisClient.hset(procKey, mapping=workerInfo)
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
            self.procsList[workerId].kill()

            # Delete the key from the dict
            del self.procsList[workerId]

            # Delete the entry from Redis
            self.redisClient.delete(workerId)
        except Exception as e:
            raise e
        return {
            'result': True,
            'msg': 'WORKER_DELETED_SUCCESS'
        }



    # Utils
    # These functions are to be used internally, and don't follow the descriptive return format laid out above.
    # TODO: Seperate these into their own module/package somehow.

    def getCreds(self, userId):
        # Hardcoded for now...
        apiKey = os.getenv("API_KEY")
        apiSecret = os.getenv("API_SECRET")

        return [apiKey, apiSecret]

    def getCurrentPort(self):
        currentPort = self.redisClient.get(self.redisKeys['currentPort'])
        if currentPort == None:
            return self.defaultWorkerPort
        else:
            currentPort = int(currentPort) + 1
            # Set the current port to the new one
            # TODO: Race condition?
            self.redisClient.set(self.redisKeys['currentPort'], currentPort)
            return currentPort
        
    # TODO: Is this even correct? I don't think scan is the correct function. Switched to KEYS...
    def checkMaxProcNumber(self):
        cursor = self.redisClient.scan(
            cursor=self.currentScanCursor,
            match=f'{procKeyPrefix}*')
        self.currentScanCursor = cursor[0]  # The updated cursor

        return True if ((len(cursor[1]) >= self.maxProcs)) else False
    
    def checkProcessExist(self, workerId):
        if (workerId in self.procsList):
            if self.procsList[workerId].is_alive():
                return True
            # I don't even understand why I thought a 'is_alive' check is needed here...
            # else:
                # raise Exception('The worker is present, but not running.')
        else:
            return False
        
    def killAllClients(self):
        """
        Kill all clients, whether they exist or not. Used for system-resets and initialisations.

        Parameters
        ----------
            N/A

        Returns
        ----------
            Bool: True if successful, False otherwise.
        """

        # Step 1: Get all the workers matching the key = 'mercuryGenesis-Client-ID-*'
        # keys = self.redisClient.keys(
        #     pattern=f'{procKeyPrefix}*')
        # No need for all the above...

        # Step 2: Itirate through the list, first trying to kill the process by using its PID in redis, then purging the records in redis.
        # for i in keys:
        #     print(f'Key: {i}')
        #     currentRecord = self.redisClient.hgetall(i)
        #     try:
        #         currentPid = currentRecord['PID']
        #         currentProc = self.procsList[i]
        #         currentProc.terminate()
        #         print(f'Killed process with PID: {currentPid}')
        #     except Exception as e:
        #         print(e)

        # Itirate through the list
        for key, proc in self.procsList.items():
            try:
                proc.terminate()
            except Exception as e:
                print(e)

        # Itirate through the redis keys
        keys = self.redisClient.keys(
            pattern=f'{procKeyPrefix}*')
        for key in keys:
            try:
                self.redisClient.delete(key)
            except Exception as e:
                print(e)

        return keys