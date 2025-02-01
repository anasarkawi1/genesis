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
# import logging


# logger = logging.getLogger('uvicorn.error')


# Exception definitions
# Here, each exception provided in HermesExceptions is inherited to a new Exception, which itself inherits a new base exception `WorkersException`.

# Workers base exception
class WorkersException():
    responseStatusCode      : int
    responseMessage         : str

#
# Exception extenstions
#

class UnknownGenericWorkersException(WorkersException, hermesExceptions.UnknownGenericHermesException):
    responseStatusCode      = 500
    responseMessage         = hermesExceptions.UnknownGenericHermesException.errStr

class AuthFailedWorkersException(WorkersException, hermesExceptions.AuthFailed):
    responseStatusCode      = 401
    responseMessage         = hermesExceptions.AuthFailed.errStr

class InsufficientParamsWorkersException(WorkersException, hermesExceptions.InsufficientParameters):
    responseStatusCode      = 400
    responseMessage         = hermesExceptions.InsufficientParameters.errStr

class InternalConErrWorkersException(WorkersException, hermesExceptions.InternalConnectionError):
    responseStatusCode      = 500
    responseMessage         = hermesExceptions.InternalConnectionError.errStr

class TooManyRequestWorkersException(WorkersException, hermesExceptions.TooManyRequests):
    responseStatusCode      = 420
    responseMessage         = hermesExceptions.TooManyRequests.errStr

class RequestTimeoutWorkersException(WorkersException, hermesExceptions.RequestTimeout):
    responseStatusCode      = 408
    responseMessage         = hermesExceptions.RequestTimeout.errStr

class GenericOrderWorkersException(WorkersException, hermesExceptions.GenericOrderError):
    responseStatusCode      = 500
    responseMessage         = hermesExceptions.GenericOrderError.errStr

class OrderFailedToSendWorkersException(WorkersException, hermesExceptions.OrderFailedToSend):
    responseStatusCode      = 502
    responseMessage         = hermesExceptions.OrderFailedToSend.errStr

class OrderRejectedWorkersException(WorkersException, hermesExceptions.OrderRejected):
    responseStatusCode      = 400
    responseMessage         = hermesExceptions.OrderRejected.errStr

class InsufficientBalanceWorkersException(WorkersException, hermesExceptions.InsufficientBalance):
    responseStatusCode      = 412
    responseMessage         = hermesExceptions.InsufficientBalance.errStr


# Type hinting definitions
class AlgorithmDict(typing.TypedDict):
    entry   : dict
    exit    : dict


def exceptionConverter(baseException):
    match baseException:
        case _:
            pass

class workerClass:

    def positionEntryHandler(self, trader: Trader):
        # Here, we need to call the order functions
        try:
            orderOut = trader.costBuy(self.entryCost)
            # Check if the entire order is executed. If not, continue checking for the rest of the order until it is  completely filled.
            if (orderOut["origQty"] != orderOut["executedQty"]):
                pass
            # print(orderOut)
            execQty = orderOut['executedQty']
            self.execQty = execQty
            print(f"Executed Qty: {execQty}")
            self.positionEntered = True
            print("Position entered!")
        
        # The except cases here will be made for each case it seems like. There gotta be a better way of doing this...
        except hermesExceptions.HermesBaseException as err:
            raise err

    def positionExitHandler(self, trader: Trader):
        orderOut = trader.sell(self.execQty)
        execQty = orderOut['executedQty']
        self.execQty = execQty
        print(f"Executed Qty: {execQty}")
        self.positionEntered = False
        print("Position exited!")

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
            entry_cost      : float

        @self.workerAPI.post('/setAlgorithm')
        async def setCurrentAlgorithm(params: SetAlgoReqBody):
            self.algorithmId    = params.algorithm_id
            self.algorithm      = params.algorithm       # Algorithm to be referenced. Also enables order placing.
            self.entryCost      = params.entry_cost
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
