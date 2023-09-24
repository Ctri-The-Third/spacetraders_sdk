from straders_sdk.client_api import SpaceTradersApiClient
from straders_sdk.ship import Ship
from straders_sdk.models import ShipMount

BASE_URL = "https://stoplight.io/mocks/spacetraders/spacetraders/96627693"


def test_ship_survey():
    client = SpaceTradersApiClient("token", BASE_URL)
    ship = Ship()
    ship.nav.status = "IN_ORBIT"
    ship.mounts.append(
        ShipMount(
            {
                "symbol": "MINING_LASER_I",
                "name": "Mining Laser",
                "desc": "Description",
                "requirements": {},
            }
        )
    )
    resp = client.ship_survey(ship)
    assert resp
