from straders_sdk.models import System
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
        self.logger = logging.getLogger(__name__)

    def to_json(self):
        return {
            "start_system": self.start_system.to_json(),
            "end_system": self.end_system.to_json(),
            "jumps": self.jumps,
            "distance": self.distance,
            "route": [system.symbol for system in self.route],
            "seconds_to_destination": self.seconds_to_destination,
            "compilation_timestamp": self.compilation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    def save_to_file(self, destination_folder: str):
        try:
            with open(
                f"{destination_folder}{self.start_system.symbol}-{self.end_system.symbol}.json",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(json.dumps(self.to_json(), indent=2))
        except Exception as e:
            self.logger.warning(
                "Failed to save route to file, does the folder %s exist? %s",
                destination_folder,
                e,
            )

    @classmethod
    def from_json(cls, json_data):
        route = cls(
            System.from_json(json_data["start_system"]),
            System.from_json(json_data["end_system"]),
            json_data["jumps"],
            json_data["distance"],
            json_data["route"],
            json_data["seconds_to_destination"],
            datetime.fromisoformat(json_data["compilation_timestamp"]),
        )
        return route
