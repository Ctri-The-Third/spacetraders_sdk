from straders_sdk.models_misc import System, Waypoint
import json
import logging
from datetime import datetime


class JumpGateRoute:
    def __init__(
        self,
        start_system: System,
        end_system: System,
        jumps: int,
        distance: float,
        route: list[str],
        seconds_to_destination: int,
        compilation_timestamp: datetime,
    ) -> None:
        pass

        self.start_system: System = start_system
        self.end_system: System = end_system
        self.jumps: int = jumps
        self.total_distance: float = distance
        self.route: list[System] = route
        self.seconds_to_destination: int = seconds_to_destination
        self.compilation_timestamp: datetime = compilation_timestamp
        self.logger = logging.getLogger(__name__)

    @property
    def distance(self):
        self.logger.warning(f"distance is deprecated, use total_distance instead")
        return self.total_distance

    def to_json(self):
        return {
            "start_system": self.start_system.to_json(),
            "end_system": self.end_system.to_json(),
            "jumps": self.jumps,
            "distance": self.total_distance,
            "route": [system.to_json() for system in self.route],
            "seconds_to_destination": self.seconds_to_destination,
            "compilation_timestamp": self.compilation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    def save_to_file(self, destination_folder: str):
        # trim waypoints out of system
        self.start_system.waypoints = []
        self.end_system.waypoints = []
        for system in self.route:
            system.waypoints = []
        try:
            with open(
                f"{destination_folder}{self.start_system.symbol}-{self.end_system.symbol}.json",
                "w",
                encoding="utf-8",
            ) as f:
                out = json.dumps(self.to_json(), indent=2)
                f.write(out)
        except Exception as e:
            self.logger.warning(
                "Failed to save intrasolar route to file, does the folder %s exist? %s",
                destination_folder,
                e,
            )

    @classmethod
    def from_json(cls, json_data):
        route_hops = [JumpGateSystem.from_json(r) for r in json_data["route"]]
        route = cls(
            System.from_json(json_data["start_system"]),
            System.from_json(json_data["end_system"]),
            json_data["jumps"],
            json_data["distance"],
            route_hops,
            json_data["seconds_to_destination"],
            datetime.fromisoformat(json_data["compilation_timestamp"]),
        )
        return route

    def __bool__(self):
        return bool(self.jumps > 0)

    def __len__(self):
        return self.jumps


class JumpGateSystem(System):
    def __init__(
        self,
        symbol: str,
        sector: str,
        type: str,
        x: float,
        y: float,
        waypoints: list[Waypoint],
        jump_gate_waypoint: Waypoint,
    ) -> None:
        super().__init__(symbol, sector, type, x, y, waypoints)
        self.jump_gate_waypoint: Waypoint = jump_gate_waypoint

    def to_json(self):
        obj = super().to_json()
        obj["gateSymbol"] = self.jump_gate_waypoint
        return obj

    @classmethod
    def from_json(cls, json_data):
        wayps = []
        for wp in json_data.get("waypoints", []):
            wp["systemSymbol"] = json_data["symbol"]
            wayps.append(Waypoint.from_json(wp))
        return cls(
            json_data["symbol"],
            json_data["sectorSymbol"],
            json_data["type"],
            json_data["x"],
            json_data["y"],
            wayps,
            json_data.get("gateSymbol", "gate_symbol_not_in_json_file"),
        )


class NavRoute(JumpGateRoute):
    def __init__(
        self,
        start_waypoint: System,
        end_waypoint: System,
        hops: int,
        total_distance: float,
        route: list[System],
        seconds_to_destination: int,
        compilation_timestamp: datetime,
        max_fuel: int,
        needs_drifting: bool,
    ) -> None:
        pass
        self.start_waypoint: Waypoint = start_waypoint
        self.end_waypoint: Waypoint = end_waypoint
        self.hops: int = hops
        self.route: list[Waypoint] = route
        self.total_distance: float = total_distance
        self.seconds_to_destination: int = seconds_to_destination
        self.compilation_timestamp: datetime = compilation_timestamp
        self.max_fuel: int = max_fuel
        self.needs_drifting: bool = needs_drifting
        self.logger = logging.getLogger("NavRoute")

    def to_json(self):
        return {
            "start_waypoint": self.start_waypoint.to_json(),
            "end_waypoint": self.end_waypoint.to_json(),
            "hops": self.hops,
            "total_distance": self.total_distance,
            "route": [waypoint for waypoint in self.route],
            "seconds_to_destination": self.seconds_to_destination,
            "compilation_timestamp": self.compilation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "max_fuel": self.max_fuel,
            "needs_drifting": self.needs_drifting,
        }

    def save_to_file(self, destination_folder: str):
        try:
            with open(
                f"{destination_folder}{self.start_waypoint.symbol}-{self.end_waypoint.symbol}[{self.max_fuel}].json",
                "w",
                encoding="utf-8",
            ) as f:
                out = json.dumps(self.to_json(), indent=2)
                f.write(out)

        except Exception as e:
            self.logger.warning(
                "Failed to save Jump Gate route to file, does the folder %s exist? %s",
                destination_folder,
                e,
            )

    @classmethod
    def from_json(cls, json_data):
        route = cls(
            Waypoint.from_json(json_data["start_waypoint"]),
            Waypoint.from_json(json_data["end_waypoint"]),
            json_data["hops"],
            json_data["total_distance"],
            json_data["route"],
            json_data["seconds_to_destination"],
            datetime.fromisoformat(json_data["compilation_timestamp"]),
            json_data["max_fuel"],
            json_data["needs_drifting"],
        )
        return route

    @classmethod
    def from_file(cls, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return cls.from_json(json_data)

    def __bool__(self):
        return self.hops > 0

    def __add__(self, other):
        if not isinstance(other, NavRoute):
            raise TypeError(
                f"unsupported operand type(s) for +: 'NavRoute' and '{type(other)}'"
            )

        if self.end_waypoint != other.start_waypoint:
            raise ValueError(
                f"Cannot add routes together, {self.end_waypoint} != {other.start_waypoint}"
            )

        new_start = self.start_waypoint
        new_end = other.end_waypoint
        new_hops = self.hops + other.hops
        new_route = self.route + other.route
        new_distance = self.total_distance + other.total_distance
        new_seconds_to_destination = (
            self.seconds_to_destination + other.seconds_to_destination
        )
        new_compilation_timestamp = datetime.now()
        new_max_fuel = max(self.max_fuel, other.max_fuel)
        new_needs_drifting = self.needs_drifting or other.needs_drifting

        return NavRoute(
            new_start,
            new_end,
            new_hops,
            new_distance,
            new_route,
            new_seconds_to_destination,
            new_compilation_timestamp,
            new_max_fuel,
            new_needs_drifting,
        )
        # self.start_waypoint: Waypoint = start_waypoint
        # self.end_waypoint: Waypoint = end_waypoint
        # self.hops: int = hops
        # self.route: list[Waypoint] = route
        # self.total_distance: float = total_distance
        # self.seconds_to_destination: int = seconds_to_destination
        # self.compilation_timestamp: datetime = compilation_timestamp
        # self.max_fuel: int = max_fuel
        # self.needs_drifting: bool = needs_drifting
        # self.logger = logging.getLogger("NavRoute")
