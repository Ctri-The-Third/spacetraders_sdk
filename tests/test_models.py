import sys

sys.path.append(".")

import pytest
from datetime import datetime, timedelta
from straders_sdk.utils import DATE_FORMAT
from straders_sdk.models import (
    Announement,
    CrewInfo,
    FuelInfo,
    ShipRequirements,
    ShipFrame,
    ShipModule,
    ShipMount,
    ShipReactor,
    ShipEngine,
    RouteNode,
    ShipRoute,
    Agent,
    Waypoint,
)

from straders_sdk.ship import Ship


# Test cases for Announement class
def test_announement():
    announcement = Announement(1, "Title", "Body")
    assert announcement.id == 1
    assert announcement.title == "Title"
    assert announcement.body == "Body"


# Test cases for other classes...


def test_crew_info():
    crew_info = CrewInfo()
    assert crew_info is not None


def test_fuel_info():
    fuel_info = FuelInfo()
    assert fuel_info is not None


def test_ship_requirements():
    ship_requirements = ShipRequirements()
    assert ship_requirements is not None
    ship_requirements = ShipRequirements(crew=1, module_slots=2, power=3)
    assert ship_requirements.crew == 1
    assert ship_requirements.module_slots == 2
    assert ship_requirements.power == 3


def test_ship_frame():
    ship_requirements = ShipRequirements(crew=1, module_slots=2, power=3)
    ship_frame = ShipFrame(
        "symbol", "name", "description", 1, 2, 3, 4, ship_requirements
    )
    assert ship_frame is not None
    assert ship_frame.symbol == "symbol"
    assert ship_frame.name == "name"
    assert ship_frame.description == "description"
    assert ship_frame.module_slots == 1
    assert ship_frame.mounting_points == 2
    assert ship_frame.fuel_capacity == 3
    assert ship_frame.condition == 4
    assert ship_frame.requirements == ship_requirements


def test_agent():
    agent = Agent("name", "location", 150, "COSMIC", 0, "acc_id")

    assert agent.account_id == "acc_id"
    assert agent.symbol == "name"

    assert agent.headquarters == "location"
    assert agent.ship_count == 0
    assert agent.credits == 150

    assert agent.starting_faction == "COSMIC"


def test_agent_from_json():
    json = {
        "accountId": "acc_id",
        "symbol": "name",
        "headquarters": "location",
        "credits": 150,
        "startingFaction": "COSMIC",
    }
    agent = Agent.from_json(json)
    assert agent.account_id == "acc_id"
    assert agent.symbol == "name"
    assert agent.headquarters == "location"
    assert agent.credits == 150
    assert agent.starting_faction == "COSMIC"


@pytest.fixture
def ship_module_json_data():
    return {
        "symbol": "S1",
        "capacity": 100,
        "range": 500,
        "name": "Ship 1",
        "description": "This is Ship 1",
        "requirements": {},
    }


def test_ship_module_init(ship_module_json_data):
    module = ShipModule(ship_module_json_data)
    assert module.symbol == "S1"
    assert module.capacity == 100
    assert module.range == 500
    assert module.name == "Ship 1"
    assert module.description == "This is Ship 1"


def test_ship_module_from_json(ship_module_json_data):
    module = ShipModule.from_json(ship_module_json_data)
    assert module.symbol == "S1"
    assert module.capacity == 100
    assert module.range == 500
    assert module.name == "Ship 1"
    assert module.description == "This is Ship 1"


def test_ship_reactor():
    requirements = ShipRequirements(crew=1, module_slots=2, power=3)
    ship_reactor = ShipReactor("symbol", "name", "description", 1, 30, requirements)
    assert ship_reactor is not None
    assert ship_reactor.symbol == "symbol"
    assert ship_reactor.name == "name"
    assert ship_reactor.description == "description"
    assert ship_reactor.condition == 1
    assert ship_reactor.power_output == 30
    assert isinstance(ship_reactor.requirements, ShipRequirements)


def test_ship_engine():
    requirements = ShipRequirements(crew=1, module_slots=2, power=3)
    ship_engine = ShipEngine("symbol", "name", "description", 1, 30, requirements)
    assert ship_engine is not None
    assert ship_engine.symbol == "symbol"
    assert ship_engine.name == "name"
    assert ship_engine.description == "description"
    assert ship_engine.condition == 1
    assert ship_engine.speed == 30
    assert isinstance(ship_engine.requirements, ShipRequirements)


def test_nav_info():
    nav_info = RouteNode("identifier", "type", "parent_system_identifier", 4, 4)
    assert nav_info is not None

    assert nav_info.symbol == "identifier"
    assert nav_info.type == "type"
    assert nav_info.systemSymbol == "parent_system_identifier"
    assert nav_info.x == 4
    assert nav_info.y == 4


def test_ship_route():
    destination = RouteNode("dest_id", "planet", "dest_sys_id", 5, 5)
    origin = RouteNode("orig_id", "planet", "orig_sys_id", 5, 5)
    departure = datetime.now()
    arrival = datetime.now() + timedelta(hours=1)
    ship_route = ShipRoute(origin, destination, departure, arrival)
    assert ship_route is not None
    assert ship_route.destination == destination
    assert ship_route.origin == origin
    assert ship_route.departure_time == departure
    assert ship_route.arrival == arrival


def test_ship_index():
    ship = Ship()
    ship.name = "CTRI-U--5"
    assert ship.index == 5

    ship.name = "CTRI-U--A"
    assert ship.index == 10

    ship.name = "CTRI-U--A0"
    assert ship.index == 160
