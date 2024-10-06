# Supervisor Module

# Import libraies
import uvicorn
import sys
from dotenv import load_dotenv

# Import API
from app import main

# Utils
from app.utilities import workersUtilities


# Load .env
load_dotenv()


def initiateAPI():
    # Start servers
    try:
        uvicorn.run(
            'app:main',
            host='0.0.0.0',
            port=8070,
            reload=True)
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

wu = workersUtilities.WorkersUtility(
    maxProcs=7,
    redisParams=redisParams,
    defaultWorkerPort=8071
)

class params:
    mode: str
    tradingPair: str
    interval: str
    exchange: str

params.mode = 'live'
params.tradingPair = 'ETHUSDT'
params.interval = '1h'
params.exchange = 'binance'

# Runtime
if __name__ == "__main__":
    # out = wu.createWorker(userId='user1', workerParams=params)
    # out = wu.checkMaxProcNumber()
    # out = wu.deleteWorker('clientId-dc084425-de99-40f7-8fff-429196ac89fc')
    # print(out)

    initiateAPI()