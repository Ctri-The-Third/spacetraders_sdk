from straders_sdk.client_api import SpaceTradersApiClient
from straders_sdk.ship import Ship
from straders_sdk.models import ShipMount
from straders_sdk.utils import ApiConfig

BASE_URL = "https://stoplight.io"
VERSION = "mocks/spacetraders/spacetraders/96627693"
TOKEN = "token"


def test_ship_survey():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()
    ship.nav.status = "IN_ORBIT"
    ship.mounts.append(
        ShipMount(
            {
                "symbol": "MOUNT_SURVEYOR_I",
                "name": "surveyor I",
                "desc": "Description",
                "requirements": {},
            }
        )
    )
    resp = client.ship_survey(ship)
    assert resp


def test_ship_scan():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()
    ship.name = "test"

    resp = client.ship_scan_ships(ship)
    assert resp


def test_ship_mount():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()

    resp = client.ship_install_mount(ship, "MINING_LASER_I")
    assert resp


def test_ship_unmount():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()

    resp = client.ship_remove_mount(ship, "MINING_LASER_I")
    assert resp


def test_ship_jumpgate():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)

    wp = client.waypoints_view_one("OE-PM")
    resp = client.system_jumpgate(wp)
    assert resp


def test_market():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)

    wp = client.waypoints_view_one("OE-PM")
    resp = client.system_market(wp)
    assert resp


def test_waypoint():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)

    wp = client.waypoints_view_one(
        "OE-PM",
    )

    assert wp


def test_construction():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)

    wp = client.waypoints_view_one(
        "OE-PM",
    )
    resp = client.system_construction(wp)
    assert resp


def test_supply_construction_site():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()
    ship.name = "test"
    wp = client.waypoints_view_one("OE-PM")
    resp = client.construction_supply(wp, ship, "CONSTRUCTION_MATERIALS", 1)

    assert resp


def test_move():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()
    ship.name = "test"
    wp = client.waypoints_view_one("OE-PM")
    resp = client.ship_move(ship, wp)

    assert resp


def test_warp():
    client = SpaceTradersApiClient("token", BASE_URL, VERSION)
    ship = Ship()
    ship.name = "test"
    wp = client.waypoints_view_one("OE-PM")
    resp = client.ship_warp(ship, wp)

    assert resp
