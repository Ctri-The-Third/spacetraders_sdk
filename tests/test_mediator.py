import os
from straders_sdk import SpaceTraders
from straders_sdk.utils import try_execute_select
from straders_sdk.models_misc import Waypoint, Market, SingletonMarkets
from straders_sdk.models_misc import JumpGate, JumpGateConnection
from straders_sdk.models_misc import ConstructionSite, ConstructionSiteMaterial
from straders_sdk.models import Ship, SingletonShips
import pytest

ST_HOST = os.getenv("ST_DB_HOST")
ST_NAME = os.getenv("ST_DB_NAME")
ST_PASS = os.getenv("ST_DB_PASSWORD")
ST_USER = os.getenv("ST_DB_USER")
ST_PORT = os.getenv("ST_DB_PORT")
TEST_AGENT_NAME = "CTRI-U-"


def test_init_possible():
    """Test if the SpaceTraders object can be initialized."""
    st = SpaceTraders("")
    assert st is not None

    st = SpaceTraders(
        "",
        db_host=ST_HOST,
        db_name=ST_NAME,
        db_pass=ST_PASS,
        db_user=ST_USER,
        db_port=ST_PORT,
    )


def test_market_singleton():
    """Test if the Market singleton is working."""

    markets = SingletonMarkets()
    market = Market("X1-MARKET-1", [], [], [])
    market.exchange = "PLACEHOLDER"
    market = markets.add_market(market)
    market2 = Market("X1-MARKET-1", [], [], [])
    market2 = markets.add_market(market2)
    assert market2.exchange != "PLACEHOLDER"


def test_ship_singleton():
    """Test if the Ship singleton is working."""

    ships = SingletonShips()
    ship = Ship()
    ship.name = "X1-SHIP-1"
    ship = ships.add_ship(ship)
    ship2 = Ship()
    ship2.name = "X1-SHIP-1"
    ship2.cargo_units_used = 30

    ship2 = ships.add_ship(ship2)
    assert ship.cargo_units_used == 30


def test_ships():
    """test all the ships we're getting out of the DB are being singletonned"""

    st = SpaceTraders(
        "",
        db_host=ST_HOST,
        db_name=ST_NAME,
        db_pass=ST_PASS,
        db_user=ST_USER,
        db_port=ST_PORT,
    )
    ships = st.ships_view()
    if (not ships) or len(ships) == 0:
        # skip the test
        pytest.skip("No ships in the DB")
    for ship in ships:
        ship: Ship
        assert ship == SingletonShips().get_ship(ship.name)

        other_ship = st.ships_view_one(ship.name)
        assert ship == other_ship
        other_ship.cargo_capacity = 5
        assert ship.cargo_capacity == 5
