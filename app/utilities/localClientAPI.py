import requests
import typing_extensions as typing
from requests import Session, Request, Response

def requestGenerator(
        session: Session,
        endpointPath,
        method: typing.Literal["GET", "POST", "PUT", "DELETE"],
        baseURL,
        defaultHeaders = None,
):
    def request(port, data = None):
        reqURL = f'{baseURL}:{port}{endpointPath}'
        reqMethod = method

        # Prepare request object
        reqObj = Request(
            reqMethod,
            url=reqURL,
            json=data,
            headers=defaultHeaders)
        preppedReq = reqObj.prepare()
        
        return session.send(preppedReq)

    # Returns the newly defined request function
    return request



class LocalClient:

    def __init__(
            self,
            baseURL = 'http://localhost'
        ):
        self.baseURL = baseURL
        self.requestsSession = Session()

        # TODO: It would be cool to specify the data shape in the protocols
        
        class GetInfoProtocol(typing.Protocol):
            def __call__(port: int) -> Response:
                ...

        # Define endpoints
        self.getInfo: GetInfoProtocol = requestGenerator(
            session=self.requestsSession,
            endpointPath='/basicInfo',
            method='GET',
            baseURL=self.baseURL
        )

        class SetAlgorithmProtocol(typing.Protocol):
            def __call__(self, port: int, data: dict) -> Response:
                ...

        # Define endpoints
        self.setAlgorithm: SetAlgorithmProtocol = requestGenerator(
            session=self.requestsSession,
            endpointPath='/setAlgorithm',
            method='POST',
            baseURL=self.baseURL
        )