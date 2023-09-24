import os
from straders_sdk.client_postgres import SpaceTradersPostgresClient
from straders_sdk.utils import try_execute_select

ST_HOST = os.getenv("ST_DB_HOST")
ST_NAME = os.getenv("ST_DB_NAME")
ST_PASS = os.getenv("ST_DB_PASSWORD")
ST_USER = os.getenv("ST_DB_USER")
ST_PORT = os.getenv("ST_DB_PORT")
TEST_AGENT_NAME = "CTRI-U-"


def test_pytest():
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
