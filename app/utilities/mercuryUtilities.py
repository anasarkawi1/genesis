import uvicorn
from mercuryFramework.trader import Trader
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import multiprocessing
from pydantic import BaseModel
import sys
import typing_extensions as typing
import numpy as np
import pandas as pd
import hermesConnector.hermesExceptions as hermesExceptions
from .blackboxInternalAPI import BlackBoxInternal
# import logging


# logger = logging.getLogger('uvicorn.error')


# Exception definitions
# Here, each exception provided in HermesExceptions is inherited to a new Exception, which itself inherits a new base exception `WorkersException`.



# Type hinting definitions
class AlgorithmDict(typing.TypedDict):
    entry   : dict
    exit    : dict




class workerClass:

    def hermesExceptionNotifier(recvException: hermesExceptions.HermesBaseException):
        pass

    def positionEntryHandler(self, trader: Trader):
        # Here, we need to call the order functions
        try:
            orderOut = trader.costBuy(self.entryCost)
            orderOrigQty = orderOut["origQty"]
            orderExecQty = orderOut["executedQty"]
            self.execQty = orderExecQty
            print(f"Executed Qty: {execQty}")

            # Check if the order was executed in full, if not, set the partial fill flag and record
            if (orderOrigQty != orderExecQty):
                # TODO: Make sure to unset this on exit!!
                self.partialFill = True
                
            self.positionEntered = True
            print("Position entered!")

            # Calculate the average fill price
            fillPriceSum = 0
            avgFillPrice = 0
            for f in orderOut["fills"]:
                fillPriceSum = fillPriceSum + f['price']
            avgFillPrice = fillPriceSum / (len(orderOut["fills"]))

            # Send the order to the backend
            self.blackboxInternal.createOrder(
                data={
                    "clientId"                  : self.workerId,
                    "userId"                    : self.workerUserId,
                    "external_order_id"         : orderOut["orderId"],
                    "price"                     : avgFillPrice,
                    "stop_price"                : 0,
                    "limit_price"               : 0,
                    "trail_price"               : 0,
                    "quantity"                  : orderExecQty,
                    "time_in_force"             : "",
                    "order_type"                : "MARKET",
                    "side"                      : "BUY",
                    "raw_json"                  : orderOut,
                    "timestamp_filled"          : f'{orderOut["transactTime"]}',
                    "partial_fill"              : self.partialFill
                })
        
        # The except cases here will be made for each case it seems like. There gotta be a better way of doing this...
        except hermesExceptions.HermesBaseException as err:
            raise err

    def positionExitHandler(self, trader: Trader):
        # TODO: Problem: Since the entire order may not be filled, does that mean the position should continue? I Support it should...
        try:
            orderOut = trader.sell(self.execQty)
            
            orderOrigQty = orderOut['origQty']
            orderExecQty = orderOut['executedQty']
            orderRemainder = 0
            partialExit = False

            # Check if the entire position has been executed
            if (orderOrigQty != orderExecQty):
                # It's a partial fill...
                # Figure out how much is remianing
                orderRemainder = orderOrigQty - orderExecQty
                self.execQty = orderRemainder
                partialExit = True
            
            if (partialExit == False):
                self.positionEntered = False
                self.execQty = 0
                partialExit = False
            
            # Reset parameters
            self.partialFill = False
            self.execQty = 0

            print(f"Executed Qty: {orderExecQty}")
            print("Position exited!")

            # Calculate the average fill price
            fillPriceSum = 0
            avgFillPrice = 0
            for f in orderOut["fills"]:
                fillPriceSum = fillPriceSum + f['price']
            avgFillPrice = fillPriceSum / (len(orderOut["fills"]))

            # Send the order to the backend
            self.blackboxInternal.createOrder(
                data={
                    "clientId"                  : self.workerId,
                    "userId"                    : self.workerUserId,
                    "external_order_id"         : orderOut["orderId"],
                    "price"                     : avgFillPrice,
                    "stop_price"                : 0,
                    "limit_price"               : 0,
                    "trail_price"               : 0,
                    "quantity"                  : orderExecQty,
                    "time_in_force"             : "",
                    "order_type"                : "MARKET",
                    "side"                      : "SELL",
                    "raw_json"                  : orderOut,
                    "timestamp_filled"          : f'{orderOut["transactTime"]}',
                    "partial_fill"              : partialExit
                })

        except hermesExceptions.HermesBaseException as err:
            raise err

    def paramChecker(
            self,
            trader              : Trader,
            dict                : dict,
            lastIndicator       : pd.Series,
            lastPrice           : pd.Series,
            callback            : callable
        ):
        for key, val in dict.items():
            if key in lastIndicator.index:
                currentVal          = lastIndicator.at[key]
                paramType           = val['param_type']
                paramDirection      = val['direction']
                thresholdVal        = val['threshold']
                compVal = 0

                if paramType == "relative":
                    compVal = currentVal
                elif paramType == "percent_diff":
                    currentClose = lastPrice.at["close"]
                    pDiff = self.percentDiff(currentVal, currentClose)
                    compVal = pDiff
                
                # These if statements check the opposite condition to fail the check
                if (compVal >= thresholdVal) and (paramDirection == "lessThan"):
                    print("Failed!")
                    return False
                elif (compVal <= thresholdVal) and (paramDirection == "greaterThan"):
                    print("Failed!")
                    return False
                        
        # Do something after the for loop finishes
        callback(trader)

    # Maybe, we can expose this to the class so it can be more readily available to the endpoints.
    def workerCallback(self, trader, lastPrice, lastIndicator):
        # Handle algorithms here
        self.lastPrice = lastPrice
        self.lastIndicator = lastIndicator

        # Check if an algorithm is set. If set, start trading.
        if self.algorithm is not None:
            # Check if a trade has been entered into already
            if self.positionEntered is False:
                # Position hasn't been entered into, look if we should enter one
                entryParams = self.algorithm['entry']
                self.paramChecker(
                    trader=trader,
                    dict=entryParams,
                    lastIndicator=lastIndicator,
                    lastPrice=lastPrice,
                    callback=self.positionEntryHandler)
            
            # A position has already been entered into, look if we should exit it.
            elif self.positionEntered is True:
                exitParams = self.algorithm["exit"]
                self.paramChecker(
                    trader=trader,
                    dict=exitParams,
                    lastIndicator=lastIndicator,
                    lastPrice=lastPrice,
                    callback=self.positionExitHandler)

            # Flush standard output
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
        self.entryCost                          = 0
        self.execQty                            = 0
        self.partialFill                        = False

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
        
        # Temporary fix. Founder mode I guess?
        self.trader.indicatorFunctionParameters = {}

        self.blackboxInternal = BlackBoxInternal()

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
            lastPrice                = self.trader.data.iloc[-1].to_dict()
            lastIndicator            = self.trader.indicatorData.iloc[-1].to_dict()
            currentDataRecieved = {
                "price"             : lastPrice,
                "indicators"        : lastIndicator,
            }
            
            return JSONResponse(
                status_code=200,
                content=currentDataRecieved
            )
        
        class SetAlgoReqBody(BaseModel):
            algorithm_id    : str
            algorithm       : dict
            entry_cost      : float

        @self.workerAPI.post('/setAlgorithm')
        async def setCurrentAlgorithm(params: SetAlgoReqBody):
            # Reset current state
            self.algorithmId        = None
            self.algorithm          = None
            self.positionEntered    = False
            self.entryCost          = 0
            self.execQty            = 0

            # Set new algo
            self.algorithmId    = params.algorithm_id
            self.algorithm      = params.algorithm       # Algorithm to be referenced. Also enables order placing.
            self.entryCost      = params.entry_cost
            # print(self.algorithm)
            print(params)
            # print("HELLOOOO???")
            sys.stdout.flush()
            return JSONResponse(status_code=200, content=self.algorithm)

        @self.workerAPI.delete('/unsetAlgorithm')
        async def unsetCurrentAlgorithm():
            self.algorithmId        = None
            self.algorithm          = None
            self.positionEntered    = False
            self.entryCost          = 0
            self.execQty            = 0
            self.partialFill        = False
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
