import uvicorn
from mercuryFramework.trader import Trader
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import multiprocessing
from pydantic import BaseModel
import sys
import typing_extensions as typing
import numpy as np
# import logging


# logger = logging.getLogger('uvicorn.error')


# Type hinting definitions
class AlgorithmDict(typing.TypedDict):
    entry   : dict
    exit    : dict


class workerClass:
    # Maybe, we can expose this to the class so it can be more readily available to the endpoints.
    def workerCallback(self, trader, lastPrice, lastIndicator):
        # Handle algorithms here
        self.lastPrice = lastPrice
        self.lastIndicator = lastIndicator
        if self.algorithm is not None:
            # An algorithm is set, start trading.
            # Check if a trade has been entered into already
            if self.positionEntered is False:
                # Position hasn't been entered into, look if we should enter one
                entryParams = self.algorithm['entry']
                for key, val in entryParams.items():
                    # Values inside val:
                    # {
                    #       'param_name'    : 'SMA20',
                    #       'param_type'    : 'relative',
                    #       'range'         : {'min': 0, 'max': 100},
                    #       'threshold'     : 20,
                    #       'direction'     : 'lessThan'
                    # }

                    # Check if the indicator exists at all
                    if key in lastIndicator.index:
                        # Indicator exists, proceed with comparison
                        # Get the current value
                        currentVal = lastIndicator.at[key]
                        # Get the algo paramter attributes
                        paramType        = val['param_type']
                        paramDirection   = val['direction']
                        thresholdVal     = val['threshold']

                        # Check if the param type
                        if paramType == "relative":
                            # Indicator is relative, check values directly
                            if (currentVal >= thresholdVal) and (paramDirection == "lessThan"):
                                print("Failed!")
                                return False
                            elif (currentVal <= thresholdVal) and (paramDirection == "greaterThan"):
                                print("Failed!")
                                return False
                        
                        elif paramType == "percent_diff":
                            # Indicator depends on the percent difference between the price and the indicator
                            currentClose = lastPrice.at["close"]
                            pDiff = self.percentDiff(currentVal, currentClose)
                            # print("*******")
                            # print(f"CURRENT: {key}")
                            # print(f"Close: {currentClose}\nValue: {currentVal}\npDiff: {pDiff}\nThreshold: {thresholdVal}")
                            
                            # These if statements check the opposite condition to fail the check
                            if (pDiff >= thresholdVal) and (paramDirection == "lessThan"):
                                # print("Failed!")
                                return False
                            elif (pDiff <= thresholdVal) and (paramDirection == "greaterThan"):
                                # print("Failed!")
                                return False
                
                # Do something after the for loop finishes
            elif self.positionEntered is True:
                # A position has already been entered into, look if we should exit it.
                pass
            print("Algorithm is set! Probably should be working right now...")
            sys.stdout.flush()
    
    def percentDiff(self, a, b):
            numerator = np.abs((a - b))
            denominator = (a + b)
            denominator = denominator / 2
            output = (numerator / denominator)
            output = output * 100
            return output

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
        self.callback                           = self.workerCallback
        self.mode                               = mode
        self.tradingPair                        = tradingPair
        self.interval                           = interval
        self.exchange                           = exchange
        self.lastPrice                          = []
        self.lastIndicator                      = []

        # Worker params
        self.workerId                           = workerId
        self.workerPort                         = workerPort
        # self.workerName                         = workerName
        self.workerUserId                       = workerUserId

        # Trading params
        self.algorithmId: str                   = None
        self.algorithm: AlgorithmDict           = None
        self.positionEntered: bool              = False

        # Supervisor params
        self.supervisorPort                     = supervisorPort

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
            algorithm       : dict

        @self.workerAPI.post('/setAlgorithm')
        async def setCurrentAlgorithm(params: SetAlgoReqBody):
            self.algorithmId    = params.algorithm_id
            self.algorithm      = params.algorithm       # Algorithm to be referenced. Also enables order placing.
            # print(self.algorithm)
            print(params)
            # print("HELLOOOO???")
            sys.stdout.flush()
            return JSONResponse(status_code=200, content=self.algorithm)
    

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
