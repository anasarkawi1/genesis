import requests
import typing_extensions as typing
from requests import Session, Request, Response
from .APIUtilities import requestGenerator


class BlackBoxInternal:
    def __init__(
            self,
            baseURL = 'http://127.0.0.1',
            port = 3020
        ):
        self.baseURL = f'{baseURL}:{port}'
        self.requestsSession = Session()

        # Test endpoint
        self.test = requestGenerator(
            session=self.requestsSession,
            endpointPath='/',
            method='GET',
            baseURL=self.baseURL
        )

        self.createOrder = requestGenerator(
            session=self.requestsSession,
            endpointPath='/orders/insert',
            method='PUT',
            baseURL=self.baseURL
        )