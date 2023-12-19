import os
from straders_sdk import SpaceTraders
from straders_sdk.utils import try_execute_select
from straders_sdk.models import Waypoint, Market
from straders_sdk.models import JumpGate, JumpGateConnection
from straders_sdk.models import ConstructionSite, ConstructionSiteMaterial
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
