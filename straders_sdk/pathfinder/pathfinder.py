import heapq
import logging
import math
import json
import os
from datetime import timedelta, datetime
from networkx import Graph
from straders_sdk.models import System, Waypoint, WaypointTrait
from networkx import Graph
from straders_sdk.utils import try_execute_select
from straders_sdk.pathfinder.route import JumpGateRoute, JumpGateSystem
from straders_sdk.pathfinder.route import NavRoute

OUTPUT_PATH = "resources/routes/"


class PathFinder:
    def __init__(self, graph=None, connection=None) -> None:
        self.logger = logging.getLogger(__name__)
        self.target_folder = OUTPUT_PATH
        self.expiration_window = timedelta(days=1)
        self.connection = connection
        self._jump_graph: Graph = None
        self._system_graph: Graph = None
        self._warp_graphs: dict = {}
        folders = ["resources", "resources/routes"]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

    @property
    def graph(self) -> Graph:
        if not self._jump_graph:
            self._jump_graph = self.load_graph_from_file()

            pass
        if not self._jump_graph:
            self._jump_graph = self.load_jump_graph_from_db()
            self.save_graph()

        return self._jump_graph

    def get_warp_graph(self, fuel_capacity) -> Graph:
        if not fuel_capacity in self._warp_graphs:
            self._warp_graphs[fuel_capacity] = self.load_graph_from_file(
                f"resources/warp_graph{fuel_capacity}.json"
            )
        if not self._warp_graphs[fuel_capacity]:
            self._warp_graphs[fuel_capacity] = self.load_warp_graph_from_db(
                fuel_capacity
            )
            self.save_graph(
                file_path=f"resources/warp_graph{fuel_capacity}.json",
                graph=self._warp_graphs[fuel_capacity],
            )
        return self._warp_graphs[fuel_capacity]

    def add_jump_gate_connection(self, system1: System, system2: System) -> None:
        self.graph.add_node(system1.symbol)
        self.graph.add_node(system2.symbol)
        self.graph.add_edge(system1.symbol, system2.symbol, weight=1)
        pass

    def calc_distance_between(self, system1: System, system2: System) -> int:
        return calc_distance_between(system1, system2)

    def h(self, current: System, goal: System, fuel_capacity=None):
        """the heuristic function for A*. note that the value given from the heuristic should be muuuch higher than the calculated cost.
        For each unit of distance (heuristic) converted into time should strongly reinforce that decision.
        """
        if fuel_capacity:
            return self.calc_travel_time_between_wps_with_fuel(
                current, goal, fuel_capacity
            )
        return (current.x - goal.x) ** 2 + (current.y - goal.y) ** 2

    def load_astar(self, start: System, end: System):
        try:
            with open(
                f"{self.target_folder}{start.symbol}-{end.symbol}.json", "r"
            ) as f:
                data = json.loads(f.read())
                return JumpGateRoute.from_json(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def load_system_nav(self, start: Waypoint, end: Waypoint, fuel_capacity: int):
        try:
            with open(
                f"{self.target_folder}{start.symbol}-{end.symbol}[{fuel_capacity}].json",
                "r",
            ) as f:
                data = json.loads(f.read())
                return NavRoute.from_json(data)
        except (FileNotFoundError, json.JSONDecodeError) as err:
            return None

    def load_graph_from_file(self, file_path="resources/graph.json") -> Graph:
        "Loads the graph from file, if it exists."
        try:
            with open(file_path, "r") as f:
                graph = Graph()
                all_data = json.loads(f.read())
                for node, data in all_data["nodes"].items():
                    graph.add_node(node, **data)

                compiled_edges = []
                for edge in all_data["edges"]:
                    compiled_edges.append([*edge])
                graph.add_edges_from(compiled_edges)
                return graph
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        except Exception as err:
            self.logger.warning(
                "Failed to load graph from file becase %s", err, exc_info=True
            )
        return None

    def determine_fuel_cost(
        self, source_wp: "Waypoint", target_wp: "Waypoint", flight_mode="CRUISE"
    ) -> int:
        "Calculate the fuel cost of a given navigation"
        speeds = {"CRUISE": 1, "DRIFT": 0, "BURN": 2, "STEALTH": 1}
        return int(
            max(
                self.calc_distance_between(source_wp, target_wp) * speeds[flight_mode],
                1,
            )
        )

    def determine_best_speed(
        self, source_wp: "Waypoint", target_wp: "Waypoint", fuel_capacity=400
    ):
        cost = self.determine_fuel_cost(source_wp, target_wp)
        if cost * 2 < fuel_capacity:
            return "BURN"
        elif cost < fuel_capacity:
            return "CRUISE"
        else:
            return "DRIFT"

    def load_jump_graph_from_db(self):
        graph = Graph()
        sql = """

with sources as ( 
select s_waypoint_Symbol, s_system_symbol, sector_symbol, s.type, s.x ,s.y
from jumpgate_connections jc 
join systems s on jc.s_system_symbol = s.system_symbol
join waypoints w on jc.s_waypoint_Symbol = w.waypoint_Symbol
	where (w.under_construction is null or w.under_construction is False) 
union
select d_waypoint_Symbol, d_system_symbol, sector_symbol, s.type, s.x ,s.y 
from jumpgate_connections jc 
join systems s on jc.d_system_symbol = s.system_symbol
join waypoints w on jc.d_waypoint_Symbol = w.waypoint_Symbol
	where (w.under_construction is null or w.under_construction is False) 
	)
select distinct * from sources 
            """

        # the graph should be populated with Systems and Connections.
        # but note that the connections themselves need to by systems.
        # sql = """SELECT symbol, sector_symbol, type, x, y FROM systems"""
        # for row in rows:
        #    syst = System(row[0], row[1], row[2], row[3], row[4], [])

        results = try_execute_select(self.connection, sql, ())

        if results:
            for result in results:
                graph.add_node(
                    result[1],
                    symbol=result[1],
                    sectorSymbol=result[2],
                    type=result[3],
                    x=result[4],
                    y=result[5],
                    gateSymbol=result[0],
                )

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
                # connections.append((nodes[row[0]], nodes[row[1]]))
                connections.append((row[0], row[1]))
                pass
            except KeyError:
                pass
                # this happens when the gate we're connected to is not one that we've scanned yet.
        if results:
            graph.add_edges_from(connections)

        return graph

    def load_warp_graph_from_db(self, fuel_capacity=400):
        "Creates a graph for a given system's refuel points, based on the waypoints in the database."
        self.logger.warning("Loading warp graph from DB - this will take a while")
        graph = Graph()
        sql = """SELECT system_symbol, sector_symbol, type, x, y,  waypoint_symbol
	FROM public.mat_intergalactic_nodes;;"""
        wayps = {}
        results = try_execute_select(self.connection, sql, ())
        if not results:
            return None
        for r in results:
            wayps[r[0]] = JumpGateSystem(r[0], r[1], r[2], r[3], r[4], [], r[5])
            graph.add_node(
                r[0],
                symbol=r[0],
                sectorSymbol=r[1],
                type=r[2],
                x=r[3],
                y=r[4],
                gateSymbol=r[5],
            )

        edge_sql = """SELECT origin_system, distance, target_waypoint, target_system
	FROM public.mat_intergalactic_edges;"""

        results = try_execute_select(self.connection, edge_sql, ())
        if not results:
            return None

        edges = []
        for r in results:
            try:
                edges.append(
                    (
                        r[0],
                        r[3],
                        {
                            "weight": _calc_travel_time_between_wps(
                                wayps[r[0]], wayps[r[3]], fuel_capacity=fuel_capacity
                            )
                        },
                    )
                )
            except KeyError:
                pass
        graph.add_edges_from(edges)
        return graph

    def load_system_graph_from_db(self, system_s: str, fuel_capacity=400):
        "Creates a graph for a given system's refuel points, based on the waypoints in the database."
        graph = Graph()
        sql = """select w.waypoint_symbol, x,y, wt.trait_symbol= 'MARKETPLACE', modifiers, under_construction  from waypoints w
left join waypoint_Traits wt on wt.waypoint_symbol = w.waypoint_symbol and wt.trait_symbol = 'MARKETPLACE'
                where system_symbol = %s
"""
        results = try_execute_select(self.connection, sql, (system_s,))
        t = [WaypointTrait("MARKETPLACE", "Marketplace", "")]
        if not results:
            return None
        wayps = {}
        for result in results:
            wayp = Waypoint(
                system_s,
                result[0],
                "",
                result[1],
                result[2],
                result[4],
                t if result[3] else [],
                {},
                {},
                [],
                result[5],
            )
            wayps[result[0]] = wayp

            graph.add_node(
                result[0],
                symbol=result[0],
                x=result[1],
                y=result[2],
                has_jump_gate=result[3],
            )
        edge_sql = """select w1.waypoint_symbol, w2.waypoint_symbol,   SQRT(POW((w2.x - w1.x), 2) + POW((w2.y - w2.y), 2)) AS distance

 from waypoints w1 
 join waypoints w2 on w1.waypoint_symbol != w2.waypoint_symbol 
 and w1.system_symbol = w2.system_Symbol 
 left join market_tradegood mt on mt.market_waypoint = w2.waypoint_symbol
 left join waypoint_traits wt on wt.waypoint_Symbol = w2.waypoint_symbol
where  
w1.system_symbol = %s 
and w2.system_symbol = %s
and (mt.symbol = 'FUEL' or wt.trait_symbol = 'MARKETPLACE')

"""
        results = try_execute_select(self.connection, edge_sql, (system_s, system_s))
        if not results:
            return None

        # (r[0], r[1], {"weight": r[2]}) for r in results if r[0] in graph.nodes and r[1] in graph.nodes
        edges = []
        for r in results:
            try:
                edges.append(
                    (
                        r[0],
                        r[1],
                        {
                            "weight": _calc_travel_time_between_wps(
                                wayps[r[0]], wayps[r[1]], fuel_capacity=fuel_capacity
                            )
                        },
                    )
                )
            except KeyError:
                pass  # connected to a node that's not in the graph? shouldn't happen, but not a huge deal.
        graph.add_edges_from(edges)
        return graph

    def save_graph(self, file_path="resources/graph.json", graph=None):
        "Save a given graph. by default it'll be the jump network, not a given system one"
        output = {"nodes": [], "edges": [], "saved": datetime.now().isoformat()}
        graph = graph or self._jump_graph
        if not graph:
            return
        nodes = {}
        for node in graph.nodes(data=True):
            nodes[node[0]] = node[1]
        edges = []
        for edge in graph.edges(data=True):
            edges.append([edge[0], edge[1], edge[2]])
        output["nodes"] = nodes
        output["edges"] = edges
        with open(file_path, "w+") as f:
            f.write(json.dumps(output))
        pass

    def clear_jump_graph(self, file_path="resources/graph.json", age=timedelta(days=1)):
        self._jump_graph = None
        try:
            graph_file = json.loads(open(file_path, "r").read())
        except FileNotFoundError:
            return
        if "saved" in graph_file:
            saved = datetime.fromisoformat(graph_file["saved"])
            if saved + age > datetime.now():
                # not old enough to delete
                return
        # is old enough, or "saved" not in graph_file

        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

        # delete graph file

    def astar(
        self,
        start: System,
        goal: System,
        bypass_check: bool = False,
        force_recalc: bool = False,
    ) -> JumpGateRoute:
        "Return the shortest route through the jump gate network between two systems."
        if not force_recalc:
            route = self.load_astar(start, goal)
            if route is not None:
                if (
                    route.compilation_timestamp
                    < datetime.now() + self.expiration_window
                ):
                    return route
        graph = self.graph

        # check if there's a graph yet. There won't be if this is very early in the restart.
        if start == goal:
            return compile_route(start, goal, [goal.symbol])
        if not graph:
            return None

        "`bypass_check` is for when we're looking for the nearest nodes to the given locations, when either the source or destination are not on the jump network."
        if not bypass_check:
            if start.symbol not in graph.nodes:
                return None
            if goal.symbol not in graph.nodes:
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
        g_score[start.symbol] = 0

        # Data structure to store the f-score (g-score + heuristic) for each node
        f_score = {node: float("inf") for node in graph.nodes}
        f_score = {}
        f_score[start.symbol] = self.h(
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
                print("Completed A* - total jumps = %s", len(total_path))
                total_path.reverse()
                final_route = compile_route(start, goal, total_path)
                final_route.save_to_file(self.target_folder)
                total_path.reverse()
                inverted_route = compile_route(goal, start, total_path)
                inverted_route.save_to_file(self.target_folder)
                total_path.reverse()
                return final_route
                # Reconstruct the shortest path
                # the path will have been filled with every other step we've taken so far.

            for neighbour_s in graph.neighbors(current.symbol):
                neighbour = graph.nodes[neighbour_s]
                if not neighbour:
                    # print(f"{current.symbol} -> neighbour {neighbour_s}  not found - maybe under construction still?")
                    continue
                neighbour = JumpGateSystem.from_json(neighbour)
                # yes, g_score is the total number of jumps to get to this node.
                tentative_global_score = g_score[current.symbol] + 1

                if tentative_global_score < g_score[neighbour_s]:
                    # what if the neighbour hasn't been g_scored yet?
                    # ah we inf'd them, so unexplored is always higher
                    # so if we're in here, neighbour is the one behind us.

                    came_from[neighbour] = current
                    g_score[neighbour_s] = tentative_global_score
                    f_score[neighbour_s] = tentative_global_score + self.h(
                        neighbour, goal
                    )
                    # print(f" checked: {neighbour_s}:\t{f_score[neighbour_s]}")
                    # this f_score part I don't quite get - we're storing number of jumps + remaining distance
                    # I can't quite visualise but but if we're popping the lowest f_score in the heap - then we get the one that's closest?
                    # which is good because if we had variable jump costs, that would be factored into the g_score - for example time.
                    # actually that's a great point, time is the bottleneck we want to cut down on, not speed.
                    # this function isn't built with that in mind tho so I'm not gonna bother _just yet_

                    # add this neighbour to the priority queue - the one with the lowest remaining distance will be the next one popped.
                    heapq.heappush(open_set, (f_score[neighbour.symbol], neighbour))
        final_route = compile_route(start, goal, [])
        final_route.jumps = -1
        final_route.save_to_file(self.target_folder)
        reversed_final_route = compile_route(goal, start, [])
        reversed_final_route.jumps = -1
        reversed_final_route.save_to_file(self.target_folder)
        return None

    def plot_warp_nav(
        self,
        start: System,
        goal: System,
        fuel_capacity: int,
        force_recalc: bool = False,
    ) -> NavRoute:
        graph = self.get_warp_graph(fuel_capacity)
        waypoint_start = Waypoint("", start.symbol, "", start.x, start.y)
        waypoint_goal = Waypoint("", goal.symbol, "", goal.x, goal.y)
        return_route = self.plot_system_nav(
            None,
            waypoint_start,
            waypoint_goal,
            fuel_capacity,
            force_recalc,
            graph=graph,
        )
        return return_route

    def plot_system_nav(
        self,
        system: str,
        start: Waypoint,
        goal: Waypoint,
        fuel_capacity: int,
        force_recalc: bool = False,
        graph=None,
    ) -> NavRoute:
        "Return the shortest route through the jump gate network between two systems."

        # load from cache
        if not force_recalc:
            cached_route = self.load_system_nav(start, goal, fuel_capacity)
            if cached_route:
                return cached_route
        if not graph:
            graph = self.load_graph_from_file(f"resources/systemgraph-{system}.json")
        if not graph:
            graph = self.load_system_graph_from_db(system, fuel_capacity)

            self.save_graph(f"resources/systemgraph-{system}.json", graph)
        graph: Graph
        # check if there's a graph yet. There won't be if this is very early in the restart.
        if start == goal:
            return compile_route(start, goal, [goal])
        if not graph:
            return None

        # f"{destination_folder}{self.start_waypoint.symbol}-{self.end_waypoint.symbol}[{self.max_fuel}].json",

        # f-score is the time of the route so far
        # g-score is the total time of the route so far
        self.logger.warning("Doing an A*")

        open_set = []
        heapq.heappush(open_set, (0, start))

        # note to self - this dictionary is setting all g_scores to infinity- they have not been calculated yet.
        g_score = {node: float("inf") for node in graph.nodes}
        g_score[start.symbol] = 0

        #
        if self.determine_fuel_cost(start, goal) < fuel_capacity:
            route = [start.symbol, goal.symbol]
            route = compile_system_route(start, goal, route, fuel_capacity, graph)
            route.save_to_file(self.target_folder)
            return route

        # this is how we reconstruct our route back.Z came from Y. Y came from X. X came from start.
        came_from = {}
        while open_set:
            # Get the node with the lowest estimated total cost from the priority queue
            current = heapq.heappop(open_set)[1]
            # print(
            #    f"NEW NODE: {current.symbol} - time to here {g_score[current.symbol]}, distance() remaining { round(self.h(current, goal),2)} km"
            # )
            # logging.debug(f"NEW NODE: {f_score[current.symbol]}")
            if current == goal:
                # first list item = destination
                total_path = [current.symbol]
                current_symbol = current.symbol
                while current_symbol in came_from:
                    # +1 list item = -1 from destination
                    current_symbol = came_from[current_symbol]
                    total_path.append(current_symbol)
                # reverse so frist list_item = source.
                logging.debug("Completed A* - total jumps = %s", len(total_path))
                total_path.reverse()
                final_route = compile_system_route(
                    start, goal, total_path, fuel_capacity, graph
                )
                final_route.save_to_file(self.target_folder)
                total_path.reverse()
                inverted_route = compile_system_route(
                    goal, start, total_path, fuel_capacity, graph
                )
                inverted_route.save_to_file(self.target_folder)
                total_path.reverse()
                return final_route
                # Reconstruct the shortest path
                # the path will have been filled with every other step we've taken so far.

            for neighbour_s, cost_d in graph[current.symbol].items():
                neighbour = graph.nodes[neighbour_s]
                if not neighbour:
                    continue
                #
                # this part needs to become flexible somehow - for system mode it needs to return waypoints
                # but when we use it to warp it'll need to return JumpGateSystems
                #

                neighbour = Waypoint(
                    "", neighbour_s, "", neighbour["x"], neighbour["y"]
                )

                # yes, g_score is the total time taken to get to this node.
                cost = cost_d["weight"]
                tentative_global_score = g_score[current.symbol] + cost

                if tentative_global_score < g_score[neighbour.symbol]:
                    # what if the neighbour hasn't been g_scored yet?
                    # ah we inf'd them, so unexplored is always higher
                    # so if we're in here, neighbour is the one behind us.

                    came_from[neighbour.symbol] = current.symbol
                    g_score[neighbour.symbol] = tentative_global_score
                    f_score = tentative_global_score + self.h(
                        neighbour, goal, fuel_capacity
                    )  # total weight + weight

                    print(f" checked: {neighbour.symbol} - {f_score}")
                    # logging.debug(f" checked: {f_score}")
                    # the f_score is the total time to get here, + remaining distance.
                    # the next node we'll get is the quickest node with the shortest distance remaining.

                    # add this neighbour to the priority queue - the one with the lowest remaining distance will be the next one popped.
                    heapq.heappush(open_set, (f_score, neighbour))
        final_route = compile_system_route(start, goal, [], fuel_capacity, self.graph)
        final_route.jumps = -1
        final_route.save_to_file(self.target_folder)
        reversed_final_route = compile_system_route(
            goal, start, [], fuel_capacity, self.graph
        )
        reversed_final_route.jumps = -1
        reversed_final_route.save_to_file(self.target_folder)
        return None

    def calc_travel_time_between_wps(
        self,
        source_wp: "Waypoint",
        target_wp: "Waypoint",
        speed=30,
        flight_mode="CRUISE",
        warp=False,
    ) -> int:
        return calc_travel_time_between_wps(
            source_wp, target_wp, speed, flight_mode, warp
        )

    def calc_travel_time_between_wps_with_fuel(
        self, start: Waypoint, end: Waypoint, speed=30, warp=False, fuel_capacity=400
    ) -> float:
        return _calc_travel_time_between_wps(start, end, speed, warp, fuel_capacity)


def _calc_travel_time_between_wps(
    start: Waypoint,
    end: Waypoint,
    speed=30,
    warp=False,
    fuel_capacity=400,
) -> float:
    """determines the travel time between two systems or waypoints, swapping flight mode if it exceeds a fuel capacity.

    Note - if either of the waypoints are not marketplaces (fuel stops), then it will assume a drift.
    """

    # since we use this for systems and at this scale can't reliably have a market expectation without charting the galaxy we need to skip the drift assumption.
    if hasattr(start, "has_market") and hasattr(end, "has_market"):
        if not (start.has_market and end.has_market):
            return calc_travel_time_between_wps(start, end, speed, "DRIFT", warp)

    distance = calc_distance_between(start, end)
    if distance >= fuel_capacity:
        return calc_travel_time_between_wps(start, end, speed, "DRIFT", warp)
    if distance < fuel_capacity / 2:
        return calc_travel_time_between_wps(start, end, speed, "BURN", warp)
    return calc_travel_time_between_wps(start, end, speed, "CRUISE", warp)


def calc_travel_time_between_wps(
    source_wp: "Waypoint",
    target_wp: "Waypoint",
    speed=30,
    flight_mode="CRUISE",
    warp=False,
) -> int:
    "determines the travel time between two systems or waypoints."

    distance = calc_distance_between(source_wp, target_wp)
    if warp:
        multiplier = {"CRUISE": 50, "DRIFT": 500, "BURN": 15, "STEALTH": 60}
    else:
        multiplier = {"CRUISE": 25, "DRIFT": 250, "BURN": 7.5, "STEALTH": 30}

    return round(
        math.floor(round(max(1, distance))) * (multiplier[flight_mode] / max(speed, 1))
        + 15
    )


def compile_system_route(
    start_wp: System,
    end_wp: System,
    route: list[System],
    fuel_capacity: int,
    graph: Graph,
) -> NavRoute:
    distance = calc_distance_between(start_wp, end_wp)
    total_distance = 0
    travel_time = 0
    last_wp = start_wp
    needs_drifting = False
    for wp in route[1:]:
        wp = graph.nodes[wp]
        new_wp = Waypoint("", wp["symbol"], "", wp["x"], wp["y"])
        new_wp.traits = (
            [WaypointTrait("MARKETPLACE", "Marketplace", "")]
            if ("has_jump_gate" in wp and wp["has_jump_gate"])
            or ("gateSymbol" in wp and wp["gateSymbol"])
            else []
        )
        travel_time += _calc_travel_time_between_wps(
            last_wp, new_wp, fuel_capacity=fuel_capacity
        )
        distance = calc_distance_between(last_wp, new_wp)
        total_distance += distance
        if distance > fuel_capacity:
            needs_drifting = True
        last_wp = new_wp
    route = NavRoute(
        start_wp,
        end_wp,
        len(route),
        total_distance,
        route,
        travel_time,
        datetime.now(),
        fuel_capacity,
        needs_drifting,
    )
    return route


def compile_route(
    start_system: System, end_system: System, route: list[System]
) -> JumpGateRoute:
    distance = calc_distance_between(start_system, end_system)
    cooldown = 0
    last_system = start_system
    for system in route[:-1]:
        # print(f"last system: {last_system.symbol} to {system.symbol}")
        cooldown += calc_distance_between(last_system, system) / 10
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


def calc_distance_between(src: System, dest: System):
    return math.sqrt((src.x - dest.x) ** 2 + (src.y - dest.y) ** 2)


if __name__ == "__main__":
    import psycopg2
    import straders_sdk.client_postgres
    from straders_sdk.utils import set_logging

    DB_HOST = os.environ.get("ST_DB_HOST", "localhost")
    DB_PORT = os.environ.get("ST_DB_PORT", "5432")
    DB_USER = os.environ.get("ST_DB_USER", "spacetraders")
    DB_NAME = os.environ.get("ST_DB_NAME", "spacetraders")
    DB_PASSWORD = os.environ.get("ST_DB_PASSWORD", "spacetraders")
    TEST_FILE = os.environ.get("ST_PATH_GRAPH", "tests/test_graph.json")
    st = straders_sdk.client_postgres.SpaceTradersPostgresClient(
        DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, "CTRI-U-", DB_PORT
    )
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    set_logging(logging.DEBUG)
    pathfinder = PathFinder(connection=connection)
    source = st.waypoints_view_one("X1-PK16-G56")
    destination = st.waypoints_view_one("X1-PK16-J64")

    fuel = 600
    time_taken = _calc_travel_time_between_wps(source, destination, fuel_capacity=fuel)
    route = pathfinder.plot_system_nav(
        "X1-PK16", source, destination, fuel, force_recalc=True
    )

    print(route.hops)
    print(route.total_distance)
    print(time_taken)
    print(route.seconds_to_destination)

    print("=== STARTING JUMP TEST ===")

    source = st.systems_view_one("X1-PK16")
    destination = st.systems_view_one("X1-SR25")
    distance = calc_distance_between(source, destination)
    route = pathfinder.astar(source, destination, force_recalc=True)

    print(route.jumps)
    print(route.total_distance)
    print(route.seconds_to_destination)
