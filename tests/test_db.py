import os
from straders_sdk.client_postgres import SpaceTradersPostgresClient
from straders_sdk.utils import try_execute_select
from straders_sdk.models import Waypoint
from straders_sdk.models import JumpGate, JumpGateConnection

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
