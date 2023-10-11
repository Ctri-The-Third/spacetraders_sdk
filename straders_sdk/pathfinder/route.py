from straders_sdk.models import System
import json
from datetime import datetime


class JumpGateRoute:
    def __init__(
        self,
        start_system: System,
        end_system: System,
        jumps: int,
        distance: float,
        route: list[System],
        seconds_to_destination: int,
        compilation_timestamp: datetime,
    ) -> None:
        pass

        self.start_system: System = start_system
        self.end_system: System = end_system
        self.jumps: int = jumps
        self.distance: float = distance
        self.route: list[System] = route
        self.seconds_to_destination: int = seconds_to_destination
        self.compilation_timestamp: datetime = compilation_timestamp

    def to_json(self):
        return {
            "start_system": self.start_system.symbol,
            "end_system": self.end_system.symbol,
            "jumps": self.jumps,
            "distance": self.distance,
            "route": [system.symbol for system in self.route],
            "seconds_to_destination": self.seconds_to_destination,
            "compilation_timestamp": self.compilation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    def save_to_file(self, destination_folder: str):
        with open(
            f"{destination_folder}{self.start_system.symbol}-{self.end_system.symbol}.json",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(self.to_json()))

    @classmethod
    def from_json(cls, json_data):
        route = cls(
            json_data["start_system"],
            json_data["end_system"],
            json_data["jumps"],
            json_data["distance"],
            json_data["route"],
            json_data["seconds_to_destination"],
            json_data["compilation_timestamp"],
        )
        return route
