from straders_sdk.pathfinder import PathFinder
from straders_sdk.models import System
import os
import psycopg2

DB_HOST = os.environ.get("ST_DB_HOST", "localhost")
DB_PORT = os.environ.get("ST_DB_PORT", "5432")
DB_USER = os.environ.get("ST_DB_USER", "spacetraders")
DB_NAME = os.environ.get("ST_DB_NAME", "spacetraders")
DB_PASSWORD = os.environ.get("ST_DB_PASSWORD", "spacetraders")
TEST_FILE = os.environ.get("ST_PATH_GRAPH", "tests/test_graph.json")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def test_pathfinder():
    pathfinder = PathFinder(connection=get_connection())
    assert pathfinder is not None
    assert pathfinder.graph is not None
    assert pathfinder.graph.nodes is not None
    assert pathfinder.graph.edges is not None


def test_pathfinder_load_from_db():
    pathfinder = PathFinder(connection=get_connection())
    assert pathfinder is not None
    assert pathfinder.graph is not None
    assert pathfinder.graph.nodes is not None
    assert pathfinder.graph.edges is not None
    assert len(pathfinder.graph.nodes) > 0
    assert len(pathfinder.graph.edges) > 0


def test_pathfinder_save_graph():
    pathfinder = PathFinder(connection=get_connection())
    pathfinder._graph = pathfinder.load_graph_from_db()
    pathfinder.save_graph()


def test_pathfinder_load_graph_from_file():
    pathfinder = PathFinder()
    assert pathfinder is not None
    graph = pathfinder.load_graph_from_file(file_path=TEST_FILE)
    assert len(graph.nodes) == 1894
    assert len(graph.edges) == 44593


def test_create_new_route():
    pathfinder = PathFinder(connection=get_connection())
    pathfinder._graph = pathfinder.load_graph_from_file(file_path=TEST_FILE)
    pathfinder._graph = pathfinder.load_graph_from_db()
    destination = System("X1-Y13", "X1", "ORANGE_STAR", -655, 14707, [])
    origin = System("X1-BG39", "X1", "ORANGE_STAR", -4299, -1102, [])
    route = pathfinder.astar(origin, destination, force_recalc=True)
    assert route is not None
    cached_route = pathfinder.astar(origin, destination, force_recalc=False)
    assert cached_route is not None