import requests
import logging
import urllib.parse
from dataclasses import dataclass
from logging import FileHandler, StreamHandler
from sys import stdout
from datetime import datetime, timedelta
import random
import time
from .local_response import LocalSpaceTradersRespose
import threading
import copy
from requests import Session
from requests_ratelimiter import LimiterSession

st_log_client: "SpaceTradersClient" = None
ST_LOGGER = logging.getLogger("API-Client")
SEND_FREQUENCY = 0.33  # 3 requests per second
SEND_FREQUENCY_VIP = 3  # for every X requests, 1 is a VIP.  to decrease the number of VIP allocations, increase this number.
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

SURVEYOR_SYMBOLS = ["MOUNT_SURVEYOR_I", "MOUNT_SURVEYOR_II", "MOUNT_SURVEYOR_III"]
MINING_SYMBOLS = [
    "MOUNT_MINING_LASER_I",
    "MOUNT_MINING_LASER_II",
    "MOUNT_MINING_LASER_III",
]
ERRROR_COOLDOWN = 4000
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
    url, page_number, params=None, headers=None, session: Session = None
) -> SpaceTradersResponse or None:
    params = params or {}
    params["page"] = page_number
    params["limit"] = 20
    return get_and_validate(url, params=params, headers=headers, session=session)


def get_and_validate_paginated(
    url,
    per_page: int,
    page_limit: int,
    params=None,
    headers=None,
    session: Session = None,
) -> SpaceTradersResponse or None:
    params = params or {}
    params["limit"] = per_page
    data = []
    for i in range(1, page_limit or 1):
        params["page"] = i
        response = get_and_validate(
            url, params=params, headers=headers, session=session
        )
        if response and response.data:
            data.extend(response.data)
        elif response:
            response.data = data
            return response
        else:
            return response
        if page_limit >= 10:
            sleep(1)
    response.data = data
    return response


def rate_limit_check(response: requests.Response):
    if response.status_code != 429:
        return


def request_and_validate(
    method,
    url,
    data=None,
    json=None,
    headers=None,
    params=None,
    session: Session = None,
) -> SpaceTradersResponse:
    if method == "GET":
        r_method = requests.get if not session else session.get
    elif method == "POST":
        r_method = requests.post if not session else session.post
    elif method == "PATCH":
        r_method = requests.patch if not session else session.patch

    else:
        return LocalSpaceTradersRespose("Method %s not supported", 0, 0, url)

    start = datetime.now()
    resp = False
    try:
        response = r_method(
            url, data=data, json=json, headers=headers, params=params, timeout=5
        )
    except (requests.exceptions.ConnectionError, TimeoutError, TypeError) as err:
        logging.error("ConnectionError: %s, %s", url, err)
        return LocalSpaceTradersRespose(
            "Could not connect!! network issue?", 404, 0, url
        )

    except Exception as err:
        logging.error("Error: %s, %s", url, err)
        return LocalSpaceTradersRespose(f"Could not connect!! {err}", 404, 0, url)
    _log_response(response)
    if response.status_code == 429:
        logging.debug("Rate limited")
        if st_log_client:
            st_log_client.log_429(url, RemoteSpaceTradersRespose(response))
        sleep(0.1)
        return post_and_validate(url, data=data, json=json, headers=headers)
    else:
        return RemoteSpaceTradersRespose(response)


def get_and_validate(
    url, params=None, headers=None, pages=None, per_page=None, session: Session = None
) -> SpaceTradersResponse or None:
    "wraps the requests.get function to make it easier to use"

    return request_and_validate("GET", url, params=params, headers=headers)


def post_and_validate(
    url, data=None, json=None, headers=None, vip=False, session: Session = None
) -> SpaceTradersResponse:
    "wraps the requests.post function to make it easier to use"

    return request_and_validate("POST", url, data=data, json=json, headers=headers)


def patch_and_validate(
    url, data=None, json=None, headers=None, session: Session = None
) -> SpaceTradersResponse:
    return request_and_validate("PATCH", url, data=data, json=json, headers=headers)


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


def waypoint_slicer(waypoint_symbol: str) -> str:
    "returns the system symbol from a waypoint symbol"
    if not waypoint_symbol:
        return None
    pieces = waypoint_symbol.split("-")
    return f"{pieces[0]}-{pieces[1]}"


def try_execute_upsert(connection, sql, params) -> LocalSpaceTradersRespose:
    if connection.closed > 1:
        logging.error("Connection is closed")
        return LocalSpaceTradersRespose(
            "Connection is closed", 0, 0, url=f"{__name__}.try_execute_upsert"
        )
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)

        return LocalSpaceTradersRespose(
            None, None, None, url=f"{__name__}.try_execute_upsert"
        )
    except Exception as err:
        logging.error("Couldn't execute upsert: %s", err)
        logging.debug("SQL: %s", sql)
        return LocalSpaceTradersRespose(
            error=err, status_code=0, error_code=0, url=f"{__name__}.try_execute_upsert"
        )


def try_execute_select(connection, sql, params) -> list:
    if connection.closed > 1:
        logging.error("Connection is closed")
        return LocalSpaceTradersRespose(
            "Connection is closed", 0, 0, url=f"{__name__}.try_execute_upsert"
        )
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows
    except Exception as err:
        logging.error("Couldn't execute select: %s", err)
        logging.debug("SQL: %s", sql)
        return LocalSpaceTradersRespose(
            error=err, status_code=0, error_code=0, url=f"{__name__}.try_execute_select"
        )


def try_execute_no_results(connection, sql, params) -> LocalSpaceTradersRespose:
    try:
        cur = connection.cursor()
        cur.execute(sql, params)
        return LocalSpaceTradersRespose(
            None, None, None, url=f"{__name__}.try_execute_no_results"
        )
    except Exception as err:
        return LocalSpaceTradersRespose(
            error=err,
            status_code=0,
            error_code=0,
            url=f"{__name__}.try_execute_no_results",
        )
