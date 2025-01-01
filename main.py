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

# redisParams = {
#     'host': '192.168.1.5',
#     'port': 6379
# }

# Runtime
if __name__ == "__main__":
    initiateAPI()