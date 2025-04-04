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
    def request(data = None):
        # reqURL = f'{baseURL}:{port}{endpointPath}'
        reqURL = f'{baseURL}{endpointPath}'
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