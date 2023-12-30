from straders_sdk.pathfinder import PathFinder
from straders_sdk.models import System, Waypoint, WaypointTrait
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
    system_graph = pathfinder.load_graph_from_file("test_system_graph-PK16.json")

    source = Waypoint(
        "X1-PK16",
        "X1-PK16-B6",
        "ORANGE_STAR",
        58,
        180,
        traits=[WaypointTrait("MARKETPLACE", "", "")],
    )

    destination = Waypoint(
        "X1-PK16",
        "X1-PK16-J64",
        "ORANGE_STAR",
        385,
        -609,
        traits=[WaypointTrait("MARKETPLACE", "", "")],
    )
    return_route = pathfinder.plot_system_nav(
        "X1-PK16", source, destination, 600, graph=system_graph, force_recalc=True
    )
    assert return_route is not None
    assert len(return_route.route) == return_route.hops
    assert return_route.total_distance == 874.8320215364918
    assert return_route.hops > 2
    assert not return_route.needs_drifting


def test_pathfinder_save_graph():
    pathfinder = PathFinder(connection=get_connection())
    pathfinder._jump_graph = pathfinder.load_jump_graph_from_db()
    pathfinder.save_graph()


def test_pathfinder_load_graph_from_file():
    pathfinder = PathFinder()
    assert pathfinder is not None
    graph = pathfinder.load_graph_from_file(file_path=TEST_FILE)
    assert len(graph.nodes) == 1398
    assert len(graph.edges) == 4942


def test_astar():
    pathfinder = PathFinder(connection=get_connection())
    pathfinder._jump_graph = pathfinder.load_graph_from_file(file_path=TEST_FILE)

    destination = System("X1-SR25", "X1", "BLUE_STAR", -2692, 11194, [])
    origin = System("X1-PK16", "X1", "RED_STAR", 16883, 4221, [])

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
