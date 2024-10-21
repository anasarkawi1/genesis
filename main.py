# Supervisor Module

# Import libraies
import uvicorn
import sys
from dotenv import load_dotenv
import time
import argparse
from fastapi import FastAPI, Response

# Import API
from app.main import app

# Utils
from app.utilities import workersUtilities

# Load .env
load_dotenv()


# app = FastAPI()
# @app.get('/')
# async def root():
#     return Response(status_code=201)


def initiateAPI():
    # Start servers
    try:
        uvicorn.run(
            'main:app', # 'app:main',
            host='0.0.0.0',
            port=8070,
            reload=True,
            lifespan='on')
        print('[INFO] Server Started!')
    except KeyboardInterrupt:
        try:
            print('[INFO] KeyboardInterrupt detected! Joining processes and exiting...')
            sys.exit(10)
        except SystemExit:
            print('Shutting down asap... one more second!')
            sys.exit(11)

redisParams = {
    'host': '192.168.1.5',
    'port': 6379
}

# wu = workersUtilities.WorkersUtility(
#     maxProcs=7,
#     redisParams=redisParams,
#     defaultWorkerPort=8071
# )

class params:
    mode: str
    tradingPair: str
    interval: str
    exchange: str

params.mode = 'live'
params.tradingPair = 'ETHUSDT'
params.interval = '1h'
params.exchange = 'binance'


def testRuntime():
    # out = wu.createWorker(userId='user1', workerParams=params)
    # out = wu.checkMaxProcNumber()
    # out = wu.deleteWorker('clientId-dc084425-de99-40f7-8fff-429196ac89fc')
    
    # outOne = wu.createWorker(userId='user1', workerParams=params)
    # wu.killAllClientsAndRecords()
    # users = ['user1', 'user2', 'user3']
    # processes = []
    # for user in users:
    #     currentProc = wu.createWorker(userId=user, workerParams=params)
    #     processes.append(currentProc)
    #     print(currentProc)
    #     pass

    time.sleep(20)

    # out = wu.killAllClientsAndRecords()
    # print(out)

    time.sleep(20)

# Runtime
if __name__ == "__main__":
    # cliParser = argparse.ArgumentParser(
    #     prog='GenesisSupervisor',
    #     description='Processor supervisor and orchestrator for mercuryFramework.',
    #     epilog='Before there was time, before there was anything, there was nothing. And before there was nothing, there were monsters...'
    # )
    # 
    # cliParser.add_argument(
    #     '-t', '--test',
    #     action='store_const',
    #     const=True,
    #     default=False,
    #     help='Executes the `testRuntime()` function inside `main.py` instead of the supervisor API. Used for internal testing purposes.') # Initiate test function instead of the API
    # args = vars(cliParser.parse_args())

    # if args['test'] == True:
    #     testRuntime()
    # else:
    #     initiateAPI()
    
    
    initiateAPI()
    # testRuntime()