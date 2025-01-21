import uvicorn
from mercuryFramework.trader import Trader
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import multiprocessing
from pydantic import BaseModel
# import logging


# logger = logging.getLogger('uvicorn.error')

class workerClass:
    # Maybe, we can expose this to the class so it can be more readily available to the endpoints.
    def workerCallback(self, trader, lastPrice, lastIndicator):
        # Handle algorithms here
        self.lastPrice = lastPrice
        self.lastIndicator = lastIndicator
        if self.algorithm is not None:
            self.logger.info('ALGORITHM SET! WE\'RE ON THE LOOK OUT!!')

    def __init__(
            self,
            apiKey,
            apiSecret,
            mode,
            tradingPair,
            interval,
            exchange,
            workerId,
            workerPort,
            workerName,
            workerUserId,
            supervisorPort,
            logger
            ):
        
        # Mercury params
        self.callback        = self.workerCallback
        self.mode            = mode
        self.tradingPair     = tradingPair
        self.interval        = interval
        self.exchange        = exchange
        self.lastPrice       = []
        self.lastIndicator   = []

        # Worker params
        self.workerId       = workerId
        self.workerPort     = workerPort
        # self.workerName     = workerName
        self.workerUserId   = workerUserId

        # Trading params
        self.algorithmId    = None
        self.algorithm      = None

        # Supervisor params
        self.supervisorPort = supervisorPort

        # Logger
        self.logger = logger


        # Instance attributes

        self.trader: Trader = Trader(
            mode            = self.mode,
            tradingPair     = self.tradingPair,
            interval        = self.interval,
            # limit           = 75,
            exchange        = self.exchange,
            credentials     = [apiKey, apiSecret],
            updateCallback  = self.callback)
        
        # Update routines
        # TODO: Implement
        def orderUpdateHandler(self):
            sPort = self.supervisorPort

        # ...we've never initialised it :,) let's see what'll happen...
        # There seems to be a problem realted to the callback... wait? could it be our callback?? (i.e. self.callback)
        # The issue seems to be stemming from the websocket update callback, specifically the line where the new calculations are appended onto the indicator df.
        # wait, we've added a new sma tho? oh god...
        # SOLVED (i think): Since I'm extremely smart I forgot to update the live price calculations with the new SMAs...
        self.trader.initialise()
        
        self.workerAPI = FastAPI()


        # Worker API Endpoints
        @self.workerAPI.get('/')
        async def root():
            return {
                'workerId': self.workerId,
                'workerPort': self.workerPort,
                'msg': 'The woker is working!'
            }
        

        @self.workerAPI.get('/basicInfo')
        async def getBasicInfo():
            return {
                "tradingPair": self.tradingPair,
                "interval": self.interval,
                "exchange": self.exchange
            }
        
        @self.workerAPI.get('/currentData')
        async def getCurrentData():
            return {
                "price": self.lastPrice,
                "indicators": self.lastIndicator
            }
        
        class SetAlgoReqBody(BaseModel):
            algorithm_id    : str
            algorithm        : dict

        @self.workerAPI.post('/setAlgorithm')
        async def setCurrentAlgorithm(params: SetAlgoReqBody):
            self.algorithmId    = params.algorithm_id
            self.algorithm      = params.algorithm       # Algorithm to be referenced. Also enables order placing.
            logger.info('JKFHDSKJFDSKLFJDLK')
            return JSONResponse(status_code=200, content={})
    

        # Server
        # TODO: MY GOD WHY AM I STUPID?? Multiprocessing library has listeners/clients for inter-process communications... also, a whole ass RESTful API is a bit overkill innit?...
        uvicorn.run(
            self.workerAPI,
            host='0.0.0.0',
            port=self.workerPort,
            log_level='critical'
        )


def createProcess(
        apiKey,
        apiSecret,
        mode,
        tradingPair,
        interval,
        exchange,
        workerId,
        workerPort,
        workerName,
        workerUserId,
        supervisorPort,
        logger
):
    return multiprocessing.Process(
        # daemon=True, # TODO: Should probably be set...
        target=workerClass,
        args=(
            apiKey,
            apiSecret,
            mode,
            tradingPair,
            interval,
            exchange,
            workerId,
            workerPort,
            workerName,
            workerUserId,
            supervisorPort,
            logger
        )
    )
