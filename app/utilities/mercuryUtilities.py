import uvicorn
from mercuryFramework.trader import Trader
from fastapi import FastAPI
import multiprocessing

class workerClass:
    # Maybe, we can expose this to the class so it can be more readily available to the endpoints.
    def workerCallback(self, trader, lastPrice, lastIndicator):
        self.lastPrice = lastPrice
        self.lastIndicator = lastIndicator

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
            workerUserId
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


        # Instance attributes

        self.trader: Trader = Trader(
            mode            = self.mode,
            tradingPair     = self.tradingPair,
            interval        = self.interval,
            # limit           = 75,
            exchange        = self.exchange,
            credentials     = [apiKey, apiSecret],
            updateCallback  = self.callback)
        
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
        
        # TODO: BEFORE MOVING FORWARD TEST THIS!!! Update: works.
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

        # TODO: Make a fucntion in mercury to give u the 


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
        workerUserId
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
            workerUserId
        )
    )
