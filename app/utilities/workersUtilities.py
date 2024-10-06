from redis import Redis
import json
from uuid import uuid4
from .mercuryUtilities import createProcess
from pydantic import BaseModel
import os


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
        self.procsList = []
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
            procKey = f'clientId-{str(uuid4())}'
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
            self.procsList.append(proc)

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

    def getWorker(self):
        pass

    def deleteWorker(self):
        pass


    # Utils

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

    def addToProcList(self):
        pass

    def checkMaxProcNumberOld(self):
        procs = self.redisClient.hgetall(self.redisKeys['procsKeys'])
        if (len(procs.keys())) >= self.maxProcs:
            return True
        else:
            return False
        
    def checkMaxProcNumber(self):
        cursor = self.redisClient.scan(
            cursor=self.currentScanCursor,
            match='clientId-*')
        self.currentScanCursor = cursor[0]  # The updated cursor

        return True if ((len(cursor[1]) >= self.maxProcs)) else False