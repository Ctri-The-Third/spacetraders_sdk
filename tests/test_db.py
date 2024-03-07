import os
from straders_sdk.client_postgres import SpaceTradersPostgresClient
from straders_sdk.utils import try_execute_select
from straders_sdk.models_misc import Waypoint, Market, System
from straders_sdk.models_misc import JumpGate, JumpGateConnection
import straders_sdk.models as st_models
from straders_sdk.models_misc import ConstructionSite, ConstructionSiteMaterial
import pytest
import psycopg2

ST_HOST = os.getenv("ST_TEST_DB_HOST", "localhost")
ST_NAME = os.getenv("ST_DB_NAME")
ST_PASS = os.getenv("ST_DB_PASSWORD")
ST_USER = os.getenv("ST_DB_USER")
ST_PORT = os.getenv("ST_DB_PORT")
TEST_AGENT_NAME = "CTRI-U-"


def test_environment_variables():
    assert ST_HOST
    assert ST_NAME
    assert ST_PASS
    assert ST_USER
    assert ST_PORT


def test_connection():
    conn = psycopg2.connect(
        dbname=ST_NAME, user=ST_USER, password=ST_PASS, host=ST_HOST, port=ST_PORT
    )
    assert conn
    conn.close()


def test_contracts():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    resp = client.view_my_contracts()

    assert isinstance(resp, list)


def test_find_waypoints_by_type():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    # get a starting system, check it for asteroid fields
    sql = "select distinct system_symbol from agents a join waypoints w on a.headquarters = w.waypoint_symbol limit 1"
    results = try_execute_select(sql)
    if len(results) == 0:
        pytest.skip("No ASTEROID waypoints found in system")
    system = results[0][0]
    resp = client.find_waypoints_by_type(system, "ASTEROID")
    assert isinstance(resp, list)

    assert resp
    for wayp in resp:
        assert wayp.type == "ASTEROID"


def test_get_jumpgates():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    test_jumpgate = JumpGate(
        "SECT-SYS-TESTJUMP", ["test_destination1", "test_destination2"]
    )
    client.update(test_jumpgate)

    wayp = Waypoint(
        "SECT-SYS", "SECT-SYS-TESTJUMP", "JUMP_GATE", 5, 5, [], [], {}, {}, [], False
    )
    jump = client.system_jumpgate(wayp)
    assert jump.waypoint_symbol == "SECT-SYS-TESTJUMP"
    assert jump.connected_waypoints == ["test_destination1", "test_destination2"]


def test_set_market(market_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    market = Market.from_json(market_response_data)
    resp = client.update(market)
    assert bool(resp)


def test_load_market(market_response_data, waypoint_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    test_waypoint = Waypoint.from_json(waypoint_response_data)
    test_market = Market.from_json(market_response_data)
    client.update(test_waypoint)
    client.update(test_market)

    actual_market = client.system_market(test_waypoint)

    assert actual_market.symbol == test_market.symbol


def test_waypoints_by_coordinate():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    targeting_query = """with co_located_waypoint_symbols as (
        select count(waypoint_symbol), system_symbol, x,y from waypoints
            group by system_symbol, x,y
            having count(waypoint_symbol) > 1 
        )
        select * from co_located_waypoint_symbols
        order by 1 desc 
        limit 1 """
    results = try_execute_select(targeting_query)
    if not results:
        pytest.skip("No co-located waypoints found")
    waypoints = client.find_waypoints_by_coords(
        results[0][1], results[0][2], results[0][3]
    )

    assert waypoints
    assert len(waypoints) > 1
    for _, w in waypoints.items():
        assert w.traits


def test_systems_view_one(system_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    test_system = System.from_json(system_response_data)
    resp = client.update(test_system)

    sys = client.systems_view_one(test_system.symbol)
    sys: System
    assert sys
    assert sys.symbol == test_system.symbol
    assert sys.waypoints
    assert sys.waypoints[0].symbol == "X1-TEST-A1"


def test_waypoint(waypoint_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    test_waypoint = Waypoint.from_json(waypoint_response_data)
    resp = client.update(test_waypoint)

    wp = client.waypoints_view_one("X1-TEST-A1")
    assert wp
    assert "STRIPPED" in wp.modifiers
    assert wp.under_construction
    for orbital in wp.orbitals:
        assert orbital["symbol"] in wp.orbital_symbols


def test_waypoints(waypoint_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    test_waypoint = Waypoint.from_json(waypoint_response_data)
    resp = client.update(test_waypoint)

    wayps = client.waypoints_view("X1-TEST")
    assert wayps
    found_waypoint = False
    for symbol, wp in wayps.items():
        assert isinstance(wp, Waypoint)
        assert wp
        if wp.symbol == test_waypoint.symbol:
            found_waypoint = True
            assert "STRIPPED" in wp.modifiers
            assert wp.under_construction

    assert found_waypoint


def test_constructionn_site(construction_response_data, waypoint_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    test_construction_site = ConstructionSite.from_json(construction_response_data)
    test_waypoint = Waypoint.from_json(waypoint_response_data)
    resp = client.update(test_construction_site)
    assert resp

    test_construction_site.materials[0].fulfilled = 4000
    resp = client.update(test_construction_site)

    loaded_construction_site = client.system_construction(test_waypoint)
    assert test_construction_site


def test_shipyard(waypoint_response_data, shipyard_response_data):
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    test_waypoint = st_models.Waypoint.from_json(waypoint_response_data)
    test_shipyard = st_models.Shipyard.from_json(shipyard_response_data)
    client.update(test_shipyard)
    loaded_shipyard = client.system_shipyard(test_waypoint)
    for ship_type, ship in loaded_shipyard.ships.items():
        assert ship.supply
    assert loaded_shipyard


@pytest.fixture
def market_response_data():
    return {
        "symbol": "X1-TEST-A1",
        "imports": [
            {
                "symbol": "FOOD",
                "name": "Galactic Cuisine",
                "description": "A diverse range of foods from different planets, including fresh produce, meats, and prepared meals.",
            },
            {
                "symbol": "JEWELRY",
                "name": "Jewelry",
                "description": "Exquisite and valuable pieces of jewelry made from rare materials and precious gems.",
            },
            {
                "symbol": "MEDICINE",
                "name": "Medicine",
                "description": "Medical products, including drugs, treatments, and medical equipment.",
            },
            {
                "symbol": "CLOTHING",
                "name": "Clothing",
                "description": "A wide range of clothing and fashion items, including garments, accessories, and textiles.",
            },
            {
                "symbol": "EQUIPMENT",
                "name": "Equipment",
                "description": "Tools and equipment used in various industries and applications.",
            },
            {
                "symbol": "MOOD_REGULATORS",
                "name": "Mood Regulators",
                "description": "Drugs or other medical treatments that are used to control or regulate mood and emotions.",
            },
        ],
        "exports": [
            {
                "symbol": "GENE_THERAPEUTICS",
                "name": "Gene Therapeutics",
                "description": "Medical treatments that use genetic engineering to treat or prevent diseases, or to enhance the human body.",
            },
            {
                "symbol": "MACHINERY",
                "name": "Machinery",
                "description": "A variety of mechanical devices and equipment, used for industrial, construction, and other practical purposes.",
            },
        ],
        "exchange": [
            {
                "symbol": "FUEL",
                "name": "Fuel",
                "description": "High-energy fuel used in spacecraft propulsion systems to enable long-distance space travel.",
            }
        ],
        "transactions": [],
        "tradeGoods": [
            {
                "symbol": "FOOD",
                "tradeVolume": 1000,
                "type": "IMPORT",
                "supply": "MODERATE",
                "activity": "WEAK",
                "purchasePrice": 534,
                "sellPrice": 262,
            },
            {
                "symbol": "JEWELRY",
                "tradeVolume": 1000,
                "type": "IMPORT",
                "supply": "LIMITED",
                "activity": "WEAK",
                "purchasePrice": 1310,
                "sellPrice": 646,
            },
            {
                "symbol": "MEDICINE",
                "tradeVolume": 1000,
                "type": "IMPORT",
                "supply": "SCARCE",
                "activity": "WEAK",
                "purchasePrice": 1250,
                "sellPrice": 620,
            },
            {
                "symbol": "CLOTHING",
                "tradeVolume": 1000,
                "type": "IMPORT",
                "supply": "SCARCE",
                "activity": "WEAK",
                "purchasePrice": 646,
                "sellPrice": 320,
            },
            {
                "symbol": "EQUIPMENT",
                "tradeVolume": 1000,
                "type": "IMPORT",
                "supply": "LIMITED",
                "activity": "WEAK",
                "purchasePrice": 1106,
                "sellPrice": 548,
            },
            {
                "symbol": "MOOD_REGULATORS",
                "tradeVolume": 100,
                "type": "IMPORT",
                "supply": "LIMITED",
                "activity": "WEAK",
                "purchasePrice": 4810,
                "sellPrice": 2360,
            },
            {
                "symbol": "GENE_THERAPEUTICS",
                "tradeVolume": 100,
                "type": "EXPORT",
                "supply": "ABUNDANT",
                "activity": "WEAK",
                "purchasePrice": 2452,
                "sellPrice": 1174,
            },
            {
                "symbol": "FUEL",
                "tradeVolume": 10,
                "type": "EXCHANGE",
                "supply": "ABUNDANT",
                "purchasePrice": 76,
                "sellPrice": 34,
            },
            {
                "symbol": "MACHINERY",
                "tradeVolume": 10,
                "type": "EXPORT",
                "supply": "HIGH",
                "activity": "WEAK",
                "purchasePrice": 364,
                "sellPrice": 168,
            },
        ],
    }


@pytest.fixture
def construction_response_data():
    return {
        "symbol": "X1-TEST-A1",
        "materials": [
            {"tradeSymbol": "FAB_MATS", "required": 4000, "fulfilled": 1200},
            {
                "tradeSymbol": "ADVANCED_CIRCUITRY",
                "required": 1200,
                "fulfilled": 1076,
            },
            {"tradeSymbol": "QUANTUM_STABILIZERS", "required": 1, "fulfilled": 1},
        ],
        "isComplete": False,
    }


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


@pytest.fixture
def shipyard_response_data():
    return {
        "symbol": "X1-TEST-A1",
        "shipTypes": [{"type": "SHIP_PROBE"}],
        "transactions": [],
        "ships": [
            {
                "type": "SHIP_PROBE",
                "name": "Probe Satellite",
                "description": "A small, unmanned spacecraft that can be launched into orbit to gather data and perform basic tasks.",
                "supply": "HIGH",
                "purchasePrice": 20848,
                "frame": {
                    "symbol": "FRAME_PROBE",
                    "name": "Probe",
                    "description": "A small, unmanned spacecraft used for exploration, reconnaissance, and scientific research.",
                    "moduleSlots": 0,
                    "mountingPoints": 0,
                    "fuelCapacity": 0,
                    "requirements": {"power": 1, "crew": 0},
                },
                "reactor": {
                    "symbol": "REACTOR_SOLAR_I",
                    "name": "Solar Reactor I",
                    "description": "A basic solar power reactor, used to generate electricity from solar energy.",
                    "powerOutput": 3,
                    "requirements": {"crew": 0},
                },
                "engine": {
                    "symbol": "ENGINE_IMPULSE_DRIVE_I",
                    "name": "Impulse Drive I",
                    "description": "A basic low-energy propulsion system that generates thrust for interplanetary travel.",
                    "speed": 3,
                    "requirements": {"power": 1, "crew": 0},
                },
                "modules": [],
                "mounts": [],
                "crew": {"required": 0, "capacity": 0},
            }
        ],
        "modificationsFee": 100,
    }
