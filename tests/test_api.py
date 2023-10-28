from straders_sdk.client_api import SpaceTradersApiClient
from straders_sdk.ship import Ship
from straders_sdk.models import ShipMount
from straders_sdk.utils import ApiConfig

BASE_URL = "https://stoplight.io/"
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

    wp = client.waypoints_view_one("OE-PM", "OE-PM-TR")
    resp = client.system_jumpgate(wp)
    assert resp
