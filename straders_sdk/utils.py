import requests
import logging
import urllib.parse
from dataclasses import dataclass
from logging import FileHandler, StreamHandler
from sys import stdout
from datetime import datetime
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


def get_and_validate(
    url, params=None, headers=None, pages=None, per_page=None, session: Session = None
) -> SpaceTradersResponse or None:
    "wraps the requests.get function to make it easier to use"
    resp = False

    try:
        if session:
            response = session.get(url, params=params, headers=headers, timeout=5)
        else:
            response = requests.get(url, params=params, headers=headers, timeout=5)
    except (
        requests.exceptions.ConnectionError,
        TimeoutError,
        TypeError,
        TimeoutError,
        requests.ReadTimeout,
    ) as err:
        logging.error("ConnectionError: %s, %s", url, err)
        return LocalSpaceTradersRespose(
            "Could not connect!! network issue?", 404, 0, url
        )

    except Exception as err:
        logging.error("Error: %s, %s", url, err)
    _log_response(response)
    if response.status_code == 429:
        if st_log_client:
            st_log_client.log_429(url, RemoteSpaceTradersRespose(response))
        logging.warning("Rate limited retrying!")
        return get_and_validate(url, params=params, headers=headers, session=session)

    if response.status_code >= 500 and response.status_code < 600:
        logging.error("SpaceTraders Server error: %s, %s", url, response.status_code)
    return RemoteSpaceTradersRespose(response)


def rate_limit_check(response: requests.Response):
    if response.status_code != 429:
        return


def request_and_validate(
    method, url, data=None, json=None, headers=None, session: Session = None
):
    if method == "GET":
        return get_and_validate(url, params=data, headers=headers, session=session)
    elif method == "POST":
        return post_and_validate(
            url, data=data, json=json, headers=headers, session=session
        )
    elif method == "PATCH":
        return patch_and_validate(
            url, data=data, json=json, headers=headers, session=session
        )
    else:
        return LocalSpaceTradersRespose("Method %s not supported", 0, 0, url)


def post_and_validate(
    url, data=None, json=None, headers=None, vip=False, session: Session = None
) -> SpaceTradersResponse:
    "wraps the requests.post function to make it easier to use"

    # repeat 5 times with staggered wait
    # if still 429, skip
    resp = False
    try:
        if session:
            response = session.post(
                url, data=data, json=json, headers=headers, timeout=5
            )
        else:
            response = requests.post(
                url, data=data, json=json, headers=headers, timeout=5
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
        return post_and_validate(
            url, data=data, json=json, headers=headers, session=session
        )
    else:
        return RemoteSpaceTradersRespose(response)


def patch_and_validate(
    url, data=None, json=None, headers=None, session: Session = None
) -> SpaceTradersResponse:
    resp = False
    try:
        if session:
            resp = session.patch(url, data=data, json=json, headers=headers, timeout=5)
        else:
            resp = requests.patch(url, data=data, json=json, headers=headers, timeout=5)
    except (requests.exceptions.ConnectionError, TimeoutError) as err:
        logging.error("ConnectionError: %s, %s", url, err)
        return None
    except Exception as err:
        logging.error("Error: %s, %s", url, err)
    _log_response(resp)
    if resp.status_code == 429:
        logging.warning("Rate limited")
        return patch_and_validate(url, data=data, json=json, headers=headers)
    else:
        return RemoteSpaceTradersRespose(resp)


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
    try:
        cur = connection.cursor()
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
    try:
        cur = connection.cursor()
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
