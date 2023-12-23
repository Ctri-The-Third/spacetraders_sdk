from straders_sdk.client_json_cache import SpaceTradersCacheClient
from straders_sdk.models import Waypoint, System
import os
import pytest

FOLDER = "resources"


def test_init():
    client = SpaceTradersCacheClient(FOLDER)
    assert client

    # check the resources folder exists
    assert os.path.exists(FOLDER)
    assert os.path.exists(os.path.join(FOLDER, "waypoints"))
    assert os.path.exists(os.path.join(FOLDER, "systems"))


def test_save_waypoint(waypoint_response_data):
    client = SpaceTradersCacheClient(FOLDER)
    wp = Waypoint.from_json(waypoint_response_data)
    client.update(wp)


def test_waypoints_view_one(waypoint_response_data):
    client = SpaceTradersCacheClient(FOLDER)
    check_wp = Waypoint.from_json(waypoint_response_data)
    wp = client.waypoints_view_one("DOESNOTEXIST")
    assert not wp

    wp = client.waypoints_view_one(check_wp.symbol)
    assert wp.symbol == check_wp.symbol


def test_save_system(system_response_data):
    client = SpaceTradersCacheClient(FOLDER)
    sys = System.from_json(system_response_data)
    client.update(sys)


def test_systems_view_one(system_response_data):
    client = SpaceTradersCacheClient(FOLDER)
    check_sys = System.from_json(system_response_data)
    sys = client.systems_view_one(check_sys.symbol)
    assert sys.symbol == check_sys.symbol
    assert len(sys.waypoints) == len(check_sys.waypoints)
    sys = client.systems_view_one("DOESNOTEXIST")
    assert not sys


def test_waypoints_view(system_response_data):
    client = SpaceTradersCacheClient(FOLDER)
    check_sys = System.from_json(system_response_data)
    wps = client.waypoints_view(check_sys.symbol)
    assert wps
    assert len(wps) == len(check_sys.waypoints)


def test_find_waypoints_by_coords(waypoint_response_data):
    client = SpaceTradersCacheClient(FOLDER)
    check_wp = Waypoint.from_json(waypoint_response_data)
    wps = client.find_waypoints_by_coords(
        check_wp.system_symbol, check_wp.x, check_wp.y
    )
    assert wps
    assert len(wps) == 3


@pytest.fixture
def waypoint_response_data():
    return {
        "systemSymbol": "X1-TEST",
        "symbol": "X1-TEST-A1",
        "type": "PLANET",
        "x": 16,
        "y": 21,
        "orbitals": [{"symbol": "X1-TEST-A3"}, {"symbol": "X1-TEST-A2"}],
        "traits": [
            {
                "symbol": "ROCKY",
                "name": "Rocky",
                "description": "A world with a rugged, rocky landscape, rich in minerals and other resources, providing a variety of opportunities for mining, research, and exploration.",
            },
            {
                "symbol": "SCATTERED_SETTLEMENTS",
                "name": "Scattered Settlements",
                "description": "A collection of dispersed communities, each independent yet connected through trade and communication networks.",
            },
            {
                "symbol": "SCARCE_LIFE",
                "name": "Scarce Life",
                "description": "A waypoint with sparse signs of life, often presenting unique challenges for survival and adaptation in a harsh environment.",
            },
            {
                "symbol": "THIN_ATMOSPHERE",
                "name": "Thin Atmosphere",
                "description": "A location with a sparse atmosphere, making it difficult to support life without specialized life-support systems.",
            },
            {
                "symbol": "METHANE_POOLS",
                "name": "Methane Pools",
                "description": "Large reservoirs of methane gas, used for fuel and in various industrial processes such as the production of hydrocarbons.",
            },
            {
                "symbol": "MAGMA_SEAS",
                "name": "Magma Seas",
                "description": "A waypoint dominated by molten rock and intense heat, creating inhospitable conditions and requiring specialized technology to navigate and harvest resources.",
            },
            {
                "symbol": "ICE_CRYSTALS",
                "name": "Ice Crystals",
                "description": "Expansive fields of ice, providing a vital source of water and other resources such as ammonia ice, liquid hydrogen, and liquid nitrogen for local populations and industries.",
            },
            {
                "symbol": "MARKETPLACE",
                "name": "Marketplace",
                "description": "A thriving center of commerce where traders from across the galaxy gather to buy, sell, and exchange goods.",
            },
        ],
        "modifiers": [
            {"symbol": "STRIPPED", "name": "string", "description": "string"}
        ],
        "chart": {"submittedBy": "VOID", "submittedOn": "2023-10-28T15:58:08.579Z"},
        "faction": {"symbol": "VOID"},
        "isUnderConstruction": True,
    }


@pytest.fixture
def system_response_data():
    return {
        "symbol": "X1-TEST",
        "sectorSymbol": "X1",
        "type": "RED_STAR",
        "x": 16883,
        "y": 4221,
        "waypoints": [
            {
                "symbol": "X1-TEST-C46",
                "type": "GAS_GIANT",
                "x": -141,
                "y": -63,
                "orbitals": [{"symbol": "X1-TEST-C47"}],
            },
            {
                "symbol": "X1-TEST-B12",
                "type": "ASTEROID",
                "x": -109,
                "y": 332,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B16",
                "type": "ASTEROID",
                "x": -333,
                "y": 98,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-G56",
                "type": "PLANET",
                "x": -63,
                "y": -10,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-E51",
                "type": "PLANET",
                "x": 49,
                "y": -24,
                "orbitals": [{"symbol": "X1-TEST-E53"}, {"symbol": "X1-TEST-E52"}],
            },
            {
                "symbol": "X1-TEST-J71",
                "type": "ASTEROID",
                "x": -557,
                "y": -528,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J77",
                "type": "ASTEROID",
                "x": 287,
                "y": -667,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B15",
                "type": "ASTEROID",
                "x": -328,
                "y": 148,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J88",
                "type": "ASTEROID",
                "x": -508,
                "y": 562,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B19",
                "type": "ASTEROID",
                "x": -338,
                "y": -34,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B27",
                "type": "ASTEROID",
                "x": -37,
                "y": -378,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B35",
                "type": "ASTEROID",
                "x": 57,
                "y": -326,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B9",
                "type": "ASTEROID",
                "x": 73,
                "y": 344,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J84",
                "type": "ASTEROID",
                "x": 79,
                "y": 785,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J66",
                "type": "ASTEROID",
                "x": -259,
                "y": 738,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B38",
                "type": "ASTEROID",
                "x": 311,
                "y": -111,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-C47",
                "type": "ORBITAL_STATION",
                "x": -141,
                "y": -63,
                "orbitals": [],
                "orbits": "X1-TEST-C46",
            },
            {
                "symbol": "X1-TEST-B6",
                "type": "FUEL_STATION",
                "x": 58,
                "y": 180,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B26",
                "type": "ASTEROID",
                "x": -123,
                "y": -356,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B33",
                "type": "ASTEROID",
                "x": 191,
                "y": -262,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-F54",
                "type": "PLANET",
                "x": 45,
                "y": 63,
                "orbitals": [{"symbol": "X1-TEST-F55"}],
            },
            {
                "symbol": "X1-TEST-B24",
                "type": "ASTEROID",
                "x": -115,
                "y": -297,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J72",
                "type": "ASTEROID",
                "x": -579,
                "y": -511,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B37",
                "type": "ASTEROID",
                "x": 169,
                "y": -329,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-H58",
                "type": "MOON",
                "x": -27,
                "y": 37,
                "orbitals": [],
                "orbits": "X1-TEST-H57",
            },
            {
                "symbol": "X1-TEST-A1",
                "type": "PLANET",
                "x": 16,
                "y": 21,
                "orbitals": [
                    {"symbol": "X1-TEST-A4"},
                    {"symbol": "X1-TEST-A3"},
                    {"symbol": "X1-TEST-A2"},
                ],
            },
            {
                "symbol": "X1-TEST-J75",
                "type": "ASTEROID",
                "x": 58,
                "y": -707,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J83",
                "type": "ASTEROID",
                "x": 66,
                "y": 786,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B17",
                "type": "ASTEROID",
                "x": -308,
                "y": -70,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-K91",
                "type": "PLANET",
                "x": 74,
                "y": -74,
                "orbitals": [{"symbol": "X1-TEST-K93"}, {"symbol": "X1-TEST-K92"}],
            },
            {
                "symbol": "X1-TEST-J68",
                "type": "ASTEROID",
                "x": -724,
                "y": 175,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B7",
                "type": "ASTEROID_BASE",
                "x": 279,
                "y": 202,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J70",
                "type": "ASTEROID",
                "x": -621,
                "y": -431,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B43",
                "type": "ASTEROID",
                "x": 220,
                "y": 304,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-F55",
                "type": "ORBITAL_STATION",
                "x": 45,
                "y": 63,
                "orbitals": [],
                "orbits": "X1-TEST-F54",
            },
            {
                "symbol": "X1-TEST-B10",
                "type": "ASTEROID",
                "x": -83,
                "y": 354,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-H57",
                "type": "PLANET",
                "x": -27,
                "y": 37,
                "orbitals": [
                    {"symbol": "X1-TEST-H58"},
                    {"symbol": "X1-TEST-H60"},
                    {"symbol": "X1-TEST-H59"},
                ],
            },
            {
                "symbol": "X1-TEST-J67",
                "type": "ASTEROID",
                "x": -701,
                "y": 315,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J73",
                "type": "ASTEROID",
                "x": -350,
                "y": -700,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B45",
                "type": "ASTEROID",
                "x": 183,
                "y": 276,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-K93",
                "type": "MOON",
                "x": 74,
                "y": -74,
                "orbitals": [],
                "orbits": "X1-TEST-K91",
            },
            {
                "symbol": "X1-TEST-D49",
                "type": "PLANET",
                "x": -1,
                "y": 84,
                "orbitals": [{"symbol": "X1-TEST-D50"}],
            },
            {
                "symbol": "X1-TEST-A4",
                "type": "ORBITAL_STATION",
                "x": 16,
                "y": 21,
                "orbitals": [],
                "orbits": "X1-TEST-A1",
            },
            {
                "symbol": "X1-TEST-J78",
                "type": "ASTEROID",
                "x": 608,
                "y": -416,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J81",
                "type": "ASTEROID",
                "x": 437,
                "y": 628,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J87",
                "type": "ASTEROID",
                "x": 367,
                "y": 611,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J63",
                "type": "FUEL_STATION",
                "x": 320,
                "y": -506,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B28",
                "type": "ASTEROID",
                "x": 16,
                "y": -375,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B34",
                "type": "ASTEROID",
                "x": 251,
                "y": -234,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-H60",
                "type": "MOON",
                "x": -27,
                "y": 37,
                "orbitals": [],
                "orbits": "X1-TEST-H57",
            },
            {
                "symbol": "X1-TEST-AE5E",
                "type": "ENGINEERED_ASTEROID",
                "x": -17,
                "y": 20,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B44",
                "type": "ASTEROID",
                "x": 291,
                "y": 206,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-E53",
                "type": "MOON",
                "x": 49,
                "y": -24,
                "orbitals": [],
                "orbits": "X1-TEST-E51",
            },
            {
                "symbol": "X1-TEST-B8",
                "type": "ASTEROID",
                "x": 168,
                "y": 286,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J82",
                "type": "ASTEROID",
                "x": 698,
                "y": 346,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J90",
                "type": "ASTEROID",
                "x": -417,
                "y": 626,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B25",
                "type": "ASTEROID",
                "x": 18,
                "y": -367,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B31",
                "type": "ASTEROID",
                "x": -192,
                "y": -284,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B41",
                "type": "ASTEROID",
                "x": 334,
                "y": -60,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-H59",
                "type": "MOON",
                "x": -27,
                "y": 37,
                "orbitals": [],
                "orbits": "X1-TEST-H57",
            },
            {
                "symbol": "X1-TEST-J79",
                "type": "ASTEROID",
                "x": 753,
                "y": -142,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J85",
                "type": "ASTEROID",
                "x": 28,
                "y": 762,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B18",
                "type": "ASTEROID",
                "x": -321,
                "y": -163,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B23",
                "type": "ASTEROID",
                "x": -51,
                "y": -372,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B30",
                "type": "ASTEROID",
                "x": -84,
                "y": -338,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B42",
                "type": "ASTEROID",
                "x": 188,
                "y": 291,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-A3",
                "type": "MOON",
                "x": 16,
                "y": 21,
                "orbitals": [],
                "orbits": "X1-TEST-A1",
            },
            {
                "symbol": "X1-TEST-J76",
                "type": "ASTEROID",
                "x": 535,
                "y": -502,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B14",
                "type": "ASTEROID",
                "x": -324,
                "y": 102,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-I62",
                "type": "FUEL_STATION",
                "x": 124,
                "y": -195,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B40",
                "type": "ASTEROID",
                "x": 343,
                "y": 178,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-K92",
                "type": "MOON",
                "x": 74,
                "y": -74,
                "orbitals": [],
                "orbits": "X1-TEST-K91",
            },
            {
                "symbol": "X1-TEST-C48",
                "type": "FUEL_STATION",
                "x": -106,
                "y": -47,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-A2",
                "type": "MOON",
                "x": 16,
                "y": 21,
                "orbitals": [],
                "orbits": "X1-TEST-A1",
            },
            {
                "symbol": "X1-TEST-B11",
                "type": "ASTEROID",
                "x": 19,
                "y": 339,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B13",
                "type": "ASTEROID",
                "x": -175,
                "y": 285,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B22",
                "type": "ASTEROID",
                "x": -327,
                "y": -122,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J69",
                "type": "ASTEROID",
                "x": -674,
                "y": -256,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B36",
                "type": "ASTEROID",
                "x": 333,
                "y": -114,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J80",
                "type": "ASTEROID",
                "x": 609,
                "y": 384,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J86",
                "type": "ASTEROID",
                "x": -94,
                "y": 743,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B21",
                "type": "ASTEROID",
                "x": -324,
                "y": -93,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J64",
                "type": "ASTEROID_BASE",
                "x": 385,
                "y": -609,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-E52",
                "type": "MOON",
                "x": 49,
                "y": -24,
                "orbitals": [],
                "orbits": "X1-TEST-E51",
            },
            {
                "symbol": "X1-TEST-J89",
                "type": "ASTEROID",
                "x": -356,
                "y": 656,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B20",
                "type": "ASTEROID",
                "x": -333,
                "y": 31,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B29",
                "type": "ASTEROID",
                "x": 25,
                "y": -352,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J74",
                "type": "ASTEROID",
                "x": -26,
                "y": -765,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-J65",
                "type": "ASTEROID",
                "x": -46,
                "y": 753,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B32",
                "type": "ASTEROID",
                "x": 170,
                "y": -274,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-B39",
                "type": "ASTEROID",
                "x": 278,
                "y": -176,
                "orbitals": [],
            },
            {
                "symbol": "X1-TEST-D50",
                "type": "MOON",
                "x": -1,
                "y": 84,
                "orbitals": [],
                "orbits": "X1-TEST-D49",
            },
            {
                "symbol": "X1-TEST-I61",
                "type": "JUMP_GATE",
                "x": 241,
                "y": -381,
                "orbitals": [],
            },
        ],
        "factions": [],
    }
