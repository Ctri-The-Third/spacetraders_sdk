from straders_sdk.pathfinder import PathFinder
from straders_sdk.models import System, Waypoint
from straders_sdk.ship import Ship
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


def test_pathfinder_system_from_db():
    pathfinder = PathFinder(connection=get_connection())
    assert pathfinder is not None
    test_graph = pathfinder.load_system_graph_from_db("X1-TEST")
    assert test_graph
    assert len(test_graph.nodes) > 0
    assert len(test_graph.edges) > 0


def test_plot_system_nav():
    pathfinder = PathFinder(connection=get_connection())
    assert pathfinder is not None
    source = Waypoint(
        "X1-U49", "X1-U49-B6", "ORANGE_STAR", -57, 342, [], [], None, None, [], False
    )
    destination = Waypoint(
        "X1-U49", "X1-U49-FA4A", "ORANGE_STAR", -25, -7, [], [], None, None, [], False
    )
    return_route = pathfinder.plot_system_nav("X1-U49", source, destination, 400)
    assert return_route is not None


def test_pathfinder_save_graph():
    pathfinder = PathFinder(connection=get_connection())
    pathfinder._jump_graph = pathfinder.load_jump_graph_from_db()
    pathfinder.save_graph()


def test_pathfinder_load_graph_from_file():
    pathfinder = PathFinder()
    assert pathfinder is not None
    graph = pathfinder.load_graph_from_file(file_path=TEST_FILE)
    assert len(graph.nodes) == 3788
    assert len(graph.edges) == 44593


def test_create_new_route():
    pathfinder = PathFinder(connection=get_connection())
    pathfinder._jump_graph = pathfinder.load_graph_from_file(file_path=TEST_FILE)
    destination = System("X1-Y13", "X1", "ORANGE_STAR", -655, 14707, [])
    origin = System("X1-BG39", "X1", "ORANGE_STAR", -4299, -1102, [])
    route = pathfinder.astar(origin, destination, force_recalc=True)
    assert route is not None
    cached_route = pathfinder.astar(origin, destination, force_recalc=False)
    assert cached_route is not None


def test_distance_calc():
    pathfinder = PathFinder(connection=get_connection())
    ship = Ship()

    first_waypoint = System("test", "test,", "test", 0, 0, [])
    second_waypoint = System("test", "test,", "test", 5, 5, [])

    distance = pathfinder.calc_distance_between(first_waypoint, second_waypoint)
    assert distance == 7.0710678118654755

    pass


def test_load_warp_graph():
    pass


def test_flight_times():
    pathfinder = PathFinder(connection=get_connection())

    first_waypoint = System("test", "test,", "test", -167, 301, [])
    second_waypoint = System("test", "test,", "test", -126, 331, [])

    cruise_time = pathfinder.calc_travel_time_between_wps(
        first_waypoint, second_waypoint, 30, "CRUISE"
    )
    assert cruise_time == 58

    drift_time = pathfinder.calc_travel_time_between_wps(
        first_waypoint, second_waypoint, 30, "DRIFT"
    )
    assert drift_time == 440

    burn_time = pathfinder.calc_travel_time_between_wps(
        first_waypoint, second_waypoint, 30, "BURN"
    )
    assert burn_time == 28
