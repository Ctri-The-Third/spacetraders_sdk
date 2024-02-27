import requests
import logging
import urllib.parse
from dataclasses import dataclass
from logging import FileHandler, StreamHandler
from sys import stdout
from datetime import datetime, timedelta
import random
import json, base64
import time
from .resp_local_resp import LocalSpaceTradersRespose
import threading
import copy
from requests import Session
from requests_ratelimiter import LimiterSession
import straders_sdk.request_consumer as rc
from .pg_connection_pool import PGConnectionPool

st_log_client: "SpaceTradersClient" = None
ST_LOGGER = logging.getLogger("API-Client")
SEND_FREQUENCY = 0.33  # 3 requests per second
SEND_FREQUENCY_VIP = 3  # for every X requests, 1 is a VIP.  to decrease the number of VIP allocations, increase this number.
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

from .responses import RemoteSpaceTradersRespose, SpaceTradersResponse


@dataclass
class ApiConfig:
    __instance = None
    base_url: str = "https://api.spacetraders.io"
    version: str = "v2"

    def __new__(cls, base_url=None, version=None):
        if cls.__instance is None:
            cls.__instance = super(ApiConfig, cls).__new__(cls)

        return cls.__instance

    def __init__(self, base_url=None, version=None):
        if base_url:
            self.base_url = base_url
        if version:
            self.version = version


def get_and_validate_page(
    url, page_number, params=None, headers=None, session: Session = None, priority=5
) -> SpaceTradersResponse or None:
    params = params or {}
    params["page"] = page_number
    params["limit"] = 20
    return get_and_validate(
        url, params=params, headers=headers, session=session, priority=priority
    )


def get_and_validate_paginated(
    url,
    per_page: int,
    page_limit: int,
    params=None,
    headers=None,
    session: Session = None,
    priority=5,
) -> SpaceTradersResponse or None:
    params = params or {}
    params["limit"] = per_page
    data = []
    for i in range(1, page_limit or 2):
        params["page"] = i
        response = get_and_validate(
            url, params=params, headers=headers, session=session, priority=priority
        )
        if response and response.data:
            data.extend(response.data)
        elif response:
            response.data = data
            return response
        else:
            return response
    if not data:
        return None
    response.data = data
    return response


def rate_limit_check(response: requests.Response):
    if response.status_code != 429:
        return


def request_and_validate(
    method, url, data=None, json=None, headers=None, params=None, priority=6
):
    if isinstance(data, dict):
        json = data
        data = None
    if priority == 6:
        logging.warning("Priority not set in url %s", url)
    request = requests.Request(
        method, url=url, data=data, json=json, headers=headers, params=params
    )
    prepared_request = request.prepare()
    packaged_request = rc.PackageedRequest(
        priority, prepared_request, threading.Event()
    )
    consumer = rc.RequestConsumer()
    consumer.queue.put((packaged_request.priority, packaged_request))
    if not consumer._consumer_thread.is_alive():
        consumer.start()
    # if a request gets stuck, the thread will never end and the ship can't be reprioritised.
    # e.g. if a ship submits a priority 6 request, it's probs never getting serviced.
    # this will def crash the thread - but it will free up the ship for any new behaviour
    packaged_request.event.wait(timeout=3600)
    return RemoteSpaceTradersRespose(
        packaged_request.response, packaged_request.priority
    )


def get_name_from_token(token: str) -> str:
    # Split the JWT into its three components

    # take the "Bearer " off the front

    header_b64, payload_b64, signature = token.split(".")

    # Base64 decode the header and payload
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))

    identifier = payload.get("identifier", None)

    return identifier


def get_date_from_token(token: str) -> str:

    header_b64, payload_b64, signature = token.split(".")

    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))

    reset_date = payload.get("reset_date", None)

    return reset_date


def get_and_validate(
    url,
    params=None,
    headers=None,
    pages=None,
    per_page=None,
    session: Session = None,
    priority=5,
) -> SpaceTradersResponse or None:
    "wraps the requests.get function to make it easier to use"

    return request_and_validate(
        "GET", url, params=params, headers=headers, priority=priority
    )


def post_and_validate(
    url, data=None, json=None, headers=None, priority=5, session: Session = None
) -> SpaceTradersResponse:
    "wraps the requests.post function to make it easier to use"
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    return request_and_validate(
        "POST", url, data=data, json=json, headers=headers, priority=priority
    )


def patch_and_validate(
    url, data=None, json=None, headers=None, session: Session = None, priority=5
) -> SpaceTradersResponse:
    return request_and_validate(
        "PATCH", url, data=data, json=json, headers=headers, priority=priority
    )


def _url(endpoint) -> str:
    "wraps the `endpoint` in the base_url and version"
    config = ApiConfig()
    return f"{config.base_url}/{config.version}/{endpoint}"


def _log_response(response: requests.Response) -> None:
    "log the response from the server"
    # time, status_code, url, error details if present
    data = response.json() if response.content else {}
    url_stub = urllib.parse.urlparse(response.url).path

    error_text = f" {data['error']['code']}{data['error']}" if "error" in data else ""
    ST_LOGGER.debug("%s %s %s", response.status_code, url_stub, error_text)


def set_logging(level=logging.INFO, filename=None):
    format = "%(asctime)s:%(levelname)s:%(threadName)s:%(name)s  %(message)s"

    log_file = filename if filename else "ShipTrader.log"
    logging.basicConfig(
        handlers=[FileHandler(log_file), StreamHandler(stdout)],
        level=level,
        format=format,
    )
    logging.getLogger("client_mediator").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pyrate_limiter.limit_context_decorator").setLevel(
        logging.WARNING
    )


def parse_timestamp(timestamp: str) -> datetime:
    ts = None

    for timestamp_format in [DATE_FORMAT, "%Y-%m-%dT%H:%M:%SZ"]:
        try:
            ts = datetime.strptime(timestamp, DATE_FORMAT)
            return ts
        except:
            pass

    try:
        ts = datetime.fromisoformat(timestamp)
        return ts
    except:
        pass
    if not ts:
        logging.error("Could not parse timestamp: %s", timestamp)
    return ts


def sleep(seconds: int):
    if seconds > 0 and seconds < 6000:
        # ST_LOGGER.info(f"Sleeping for {seconds} seconds")
        time.sleep(seconds)


def sleep_until_ready(ship: "Ship"):
    sleep(max(ship.seconds_until_cooldown, ship.nav.travel_time_remaining))


def waypoint_to_system(waypoint_symbol: str) -> str:
    "returns the system symbol from a waypoint symbol"
    if "-" not in waypoint_symbol:
        return waypoint_symbol
    if not waypoint_symbol:
        return None
    pieces = waypoint_symbol.split("-")
    return f"{pieces[0]}-{pieces[1]}"


def waypoint_suffix(anything: str) -> str:
    "returns the text after the last - in a given string"
    if not anything:
        return ""
    pieces = anything.split("-")
    return pieces[-1]


def try_execute_upsert(sql="", params=(), connection=None) -> LocalSpaceTradersRespose:
    skip_return = connection is not None

    if not connection:
        logging.warning("try_execute_upsert is falling back to the connection pool.")
        connection = PGConnectionPool().get_connection()

    if connection.closed > 1:
        logging.error("Connection is closed")
        connection = PGConnectionPool().get_connection()
        skip_return = False

    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)
        connection.commit()
        return LocalSpaceTradersRespose(
            None, None, None, url=f"{__name__}.try_execute_upsert"
        )
    except Exception as err:
        logging.error("Couldn't execute upsert: %s", err)
        logging.debug("SQL: %s", sql)
        return LocalSpaceTradersRespose(
            error=err, status_code=0, error_code=0, url=f"{__name__}.try_execute_upsert"
        )
    finally:
        if not skip_return:
            PGConnectionPool().return_connection(connection)


def try_execute_select(sql="", params=(), connection=None) -> list:
    "Takes a connection from the connection pool, executes the select, and returns a list of rows - or a response object on failure"
    skip_return = connection is not None

    if not connection:
        logging.warning("try_execute_upsert is falling back to the connection pool.")
        connection = PGConnectionPool().get_connection()

    if connection.closed > 1:
        logging.error("Connection is closed - using temp")
        connection = PGConnectionPool().get_connection()
        skip_return = False

    for i in range(0, 3):
        try:
            with connection.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                resp = rows
                break
        except Exception as err:
            logging.error("Couldn't execute select - attempting again: %s", err)

            logging.debug("SQL: %s", sql)
            resp = LocalSpaceTradersRespose(
                error=err,
                status_code=0,
                error_code=0,
                url=f"{__name__}.try_execute_upsert",
            )
            time.sleep(i**1.5)
        finally:
            if not skip_return:
                PGConnectionPool().return_connection(connection)
    return resp


def try_execute_no_results(sql, params, connection) -> LocalSpaceTradersRespose:
    return try_execute_upsert(sql, params, connection)
