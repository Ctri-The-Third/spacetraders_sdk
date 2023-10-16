import heapq
import logging
import math
import json
from datetime import timedelta, datetime
from networkx import Graph
from straders_sdk.models import System
from networkx import Graph
from straders_sdk.utils import try_execute_select
from straders_sdk.pathfinder.route import JumpGateRoute

OUTPUT_PATH = "resources/routes/"


class PathFinder:
    def __init__(self, graph=None, connection=None) -> None:
        self.logger = logging.getLogger(__name__)
        self.target_folder = OUTPUT_PATH
        self.expiration_window = timedelta(days=1)
        self.connection = connection
        self._graph: Graph = None
        pass

    @property
    def graph(self) -> Graph:
        if not self._graph:
            self._graph = self.load_graph_from_file()
        if not self._graph:
            self._graph = self.load_graph_from_db()
            self.save_graph()

        return self._graph

    def add_jump_gate_connection(self, system1: System, system2: System) -> None:
        self.graph.add_node(system1.symbol)
        self.graph.add_node(system2.symbol)
        self.graph.add_edge(system1.symbol, system2.symbol, weight=1)
        pass

    def get_distance_between(self, system1: System, system2: System) -> int:
        return math.sqrt((system1.x - system2.x) ** 2 + (system1.y - system2.y) ** 2)

    def h(self, start: System, goal: System):
        return ((start.x - goal.x) ** 2 + (start.y - goal.y) ** 2) ** 0.5

    def load_astar(self, start: System, end: System):
        try:
            with open(
                f"{self.target_folder}{start.symbol}-{end.symbol}.json", "r"
            ) as f:
                data = json.loads(f.read())
                return JumpGateRoute.from_json(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def load_graph_from_file(self, file_path="resources/graph.json") -> Graph:
        try:
            with open(file_path, "r") as f:
                data = json.loads(f.read())
                systems = {
                    node["symbol"]: System.from_json(node) for node in data["nodes"]
                }
                graph = Graph()
                graph.add_nodes_from(systems)
                compiled_edges = []
                for edge in data["edges"]:
                    try:
                        compiled_edges.append([systems[edge[0]], systems[edge[1]]])
                    except KeyError:
                        continue
                graph.add_edges_from(data["edges"])
                return graph
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        except Exception as err:
            self.logger.warning(
                "Failed to load graph from file becase %s", err, exc_info=True
            )
        return None

    def load_graph_from_db(self):
        graph = Graph()
        sql = """
            select s_system_symbol, sector_symbol, type, x ,y 
            from jumpgate_connections jc 
            join systems s on jc.s_system_symbol = s.system_symbol
            """

        # the graph should be populated with Systems and Connections.
        # but note that the connections themselves need to by systems.
        # sql = """SELECT symbol, sector_symbol, type, x, y FROM systems"""
        # for row in rows:
        #    syst = System(row[0], row[1], row[2], row[3], row[4], [])

        results = try_execute_select(self.connection, sql, ())

        if results:
            nodes = {
                row[0]: System(row[0], row[1], row[2], row[3], row[4], [])
                for row in results
            }
            graph.add_nodes_from(nodes)

        else:
            return graph
        sql = """select s_system_symbol, d_system_symbol from jumpgate_connections 
                """
        results = try_execute_select(self.connection, sql, ())
        connections = []
        if not results:
            return graph
        for row in results:
            try:
                connections.append((nodes[row[0]], nodes[row[1]]))
            except KeyError:
                pass
                # this happens when the gate we're connected to is not one that we've scanned yet.
        if results:
            graph.add_edges_from(connections)
        return graph

    def save_graph(self, file_path="resources/graph.json"):
        output = {"nodes": [], "edges": [], "saved": datetime.now().isoformat()}
        graph = self._graph
        nodes = {}
        System
        for edge in graph.edges:
            nodes[edge[0].symbol] = edge[0].to_json()
            nodes[edge[1].symbol] = edge[1].to_json()
            output["edges"].append([edge[0].symbol, edge[1].symbol])
        output["nodes"] = list(nodes.values())
        with open(file_path, "w+") as f:
            f.write(json.dumps(output, indent=4))
        pass

    def astar(
        self,
        start: System,
        goal: System,
        bypass_check: bool = False,
        force_recalc: bool = False,
    ) -> JumpGateRoute:
        graph = self.graph
        if not force_recalc:
            route = self.load_astar(start, goal)
            if route is not None:
                if (
                    route.compilation_timestamp
                    < datetime.now() + self.expiration_window
                ):
                    return route
        # check if there's a graph yet. There won't be if this is very early in the restart.
        if start == goal:
            return compile_route(start, goal, [goal.symbol])
        if not graph:
            return None

        "`bypass_check` is for when we're looking for the nearest nodes to the given locations, when either the source or destination are not on the jump network."
        if not bypass_check:
            if start not in graph.nodes:
                return None
            if goal not in graph.nodes:
                return None
        # freely admit used chatgpt to get started here.

        # Priority queue to store nodes based on f-score (priority = f-score)
        # C'tri note - I think this will be 1 for all edges?
        # Update - no, F-score is the distance between the specific node and the start
        self.logger.warning("Doing an A*")

        open_set = []
        heapq.heappush(open_set, (0, start))

        # note to self - this dictionary is setting all g_scores to infinity- they have not been calculated yet.
        g_score = {node: float("inf") for node in graph.nodes}
        g_score[start] = 0

        # Data structure to store the f-score (g-score + heuristic) for each node
        f_score = {node: float("inf") for node in graph.nodes}
        f_score[start] = self.h(
            start, goal
        )  # heuristic function - standard straight-line X/Y distance

        # this is how we reconstruct our route back.Z came from Y. Y came from X. X came from start.
        came_from = {}
        while open_set:
            # Get the node with the lowest estimated total cost from the priority queue
            current = heapq.heappop(open_set)[1]
            # print(f"NEW NODE: {f_score[current]}")
            if current == goal:
                # first list item = destination
                total_path = [current]
                while current in came_from:
                    # +1 list item = -1 from destination
                    current = came_from[current]
                    total_path.append(current)
                # reverse so frist list_item = source.
                logging.debug("Completed A* - total jumps = %s", len(total_path))

                final_route = compile_route(start, goal, total_path)
                final_route.save_to_file(self.target_folder)
                total_path.reverse()
                inverted_route = compile_route(goal, start, total_path)
                inverted_route.save_to_file(self.target_folder)
                total_path.reverse()
                return final_route
                # Reconstruct the shortest path
                # the path will have been filled with every other step we've taken so far.

            for neighbour in graph.neighbors(current):
                # yes, g_score is the total number of jumps to get to this node.
                tentative_global_score = g_score[current] + 1

                if tentative_global_score < g_score[neighbour]:
                    # what if the neighbour hasn't been g_scored yet?
                    # ah we inf'd them, so unexplored is always higher
                    # so if we're in here, neighbour is the one behind us.

                    came_from[neighbour] = current
                    g_score[neighbour] = tentative_global_score
                    f_score[neighbour] = tentative_global_score + self.h(
                        neighbour, goal
                    )
                    # print(f" checked: {f_score[neighbour]}")
                    # this f_score part I don't quite get - we're storing number of jumps + remaining distance
                    # I can't quite visualise but but if we're popping the lowest f_score in the heap - then we get the one that's closest?
                    # which is good because if we had variable jump costs, that would be factored into the g_score - for example time.
                    # actually that's a great point, time is the bottleneck we want to cut down on, not speed.
                    # this function isn't built with that in mind tho so I'm not gonna bother _just yet_

                    # add this neighbour to the priority queue - the one with the lowest remaining distance will be the next one popped.
                    heapq.heappush(open_set, (f_score[neighbour], neighbour))
        final_route = compile_route(start, goal, [])
        final_route.jumps = -1
        final_route.save_to_file(self.target_folder)
        reversed_final_route = compile_route(goal, start, [])
        reversed_final_route.jumps = -1
        reversed_final_route.save_to_file(self.target_folder)
        return None


def compile_route(
    start_system: System, end_system: System, route: list[System]
) -> JumpGateRoute:
    distance = calculate_distance(start_system, end_system)
    cooldown = 0
    last_system = start_system
    for system in route[:-1]:
        print(f"last system: {last_system.symbol} to {system.symbol}")
        cooldown += calculate_distance(last_system, system) / 10
        last_system = system
    route = JumpGateRoute(
        start_system,
        end_system,
        len(route),
        distance,
        route,
        cooldown,
        datetime.now(),
    )
    return route


def calculate_distance(src: System, dest: System):
    return math.sqrt((src.x - dest.x) ** 2 + (src.y - dest.y) ** 2)
