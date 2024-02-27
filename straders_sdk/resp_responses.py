import requests
import json
from typing import Protocol, runtime_checkable
from json import JSONDecodeError
import logging

# We have just turn the Ship into a client (so it can do things like move, buy sell)
# however now it also needs responses, which has caused a circular import.
# now presently we have one class per kind of response.
# research suggests I need abstracts for this, which I really want to avoid!
# GitHub copilot autosuggested: "this is a bit of a pain, but it will be worth it in the end." :sob:


# I've looked at a couple of libraries by peers. In one case, they don't bother with a custom Response class at all, they just .update() the ship based on the json.
# as a design pattern, this avoids the circular import and lets the ship remain an interactive
# as such, I'm keeping these classes for posterity, but going to switch to the update/ from_json pattern.
@runtime_checkable
class SpaceTradersResponse(Protocol):
    data: dict
    url: str
    response_json: dict
    error: str
    status_code: int
    error_code: int
    request_proirity: int

    def __bool__(self):
        pass


class RemoteSpaceTradersRespose:
    "base class for all responses"

    def __init__(self, response: requests.Response, priority: int = None):
        self.data = {}
        self.url = response.url
        self.error = None

        self.error_code = None
        self.request_priority = None

        if response is None:
            self.status_code = 0
            self.error_code = 0
            self.error = "Timed out waiting for request to be sent."
            return

        self.status_code = response.status_code
        if response.status_code == 204 or response.content == b"":
            self.response_json = {}
        else:
            try:
                self.response_json = json.loads(response.content)
            except JSONDecodeError:
                self.response_json = {}
                logging.error(
                    "SPACE TRADERS REPSONSE DIDN'T HAVE VALID JSON URL: %s,  status code: %s, received content: %s",
                    response.url,
                    response.status_code,
                    response.content,
                )

        if "error" in self.response_json:
            self.error_parse()
        else:
            self.data = self.response_json.get("data", {})

    def error_parse(self):
        "takes the response object and parses it an error response was sent"

        self.error = self.response_json["error"]["message"]
        self.error_code = self.response_json["error"]["code"]
        if "data" in self.response_json["error"]:
            self.data = self.response_json["error"]["data"]

        if "data" in self.response_json["error"]:
            self.response_json["error"]["data"]: dict
            for key, value in self.response_json["error"]["data"].items():
                self.error += f"\n  {key}: {value}"

    def __bool__(self):
        return self.error_code is None
