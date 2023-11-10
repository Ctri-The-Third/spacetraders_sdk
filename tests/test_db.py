import os
from straders_sdk.client_postgres import SpaceTradersPostgresClient
from straders_sdk.utils import try_execute_select
from straders_sdk.models import Waypoint, Market
from straders_sdk.models import JumpGate, JumpGateConnection
import pytest

ST_HOST = os.getenv("ST_DB_HOST")
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


def test_contracts():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )
    resp = client.view_my_contracts()
    assert resp


def test_find_waypoints_by_type():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    # get a starting system, check it for asteroid fields
    sql = "select distinct system_symbol from agents a join waypoints w on a.headquarters = w.waypoint_symbol limit 1"
    system = try_execute_select(client.connection, sql, ())[0][0]
    resp = client.find_waypoints_by_type(system, "ASTEROID_FIELD")
    assert resp
    for wayp in resp:
        assert wayp.type == "ASTEROID_FIELD"


def test_get_jumpgates():
    client = SpaceTradersPostgresClient(
        ST_HOST, ST_NAME, ST_USER, ST_PASS, TEST_AGENT_NAME, db_port=ST_PORT
    )

    test_jumpgate = JumpGate(
        "SECT-SYS-TESTJUMP", ["test_destination1", "test_destination2"]
    )
    client.update(test_jumpgate)

    wayp = Waypoint("SECT-SYS", "SECT-SYS-TESTJUMP", "JUMP_GATE", 5, 5, [], [], {}, {})
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
    connection = client.connection
    results = try_execute_select(connection, targeting_query, ())
    if not results:
        pytest.skip("No co-located waypoints found")
    waypoints = client.find_waypoints_by_coords(
        results[0][1], results[0][2], results[0][3]
    )

    assert waypoints
    assert len(waypoints) > 1
    for _, w in waypoints.items():
        assert w.traits


@pytest.fixture
def market_response_data():
    return {
        "symbol": "X1-QV47-A1",
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
def waypoint_response_data():
    return {
        "systemSymbol": "X1-QV47",
        "symbol": "X1-QV47-A1",
        "type": "PLANET",
        "x": 17,
        "y": 18,
        "orbitals": [{"symbol": "X1-QV47-A3"}, {"symbol": "X1-QV47-A2"}],
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
        "modifiers": [],
        "chart": {"submittedBy": "VOID", "submittedOn": "2023-10-28T15:58:08.579Z"},
        "faction": {"symbol": "VOID"},
        "isUnderConstruction": False,
    }
