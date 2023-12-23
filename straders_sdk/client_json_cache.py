from typing import Protocol
from .models import Waypoint, Survey, Market, System
from .responses import SpaceTradersResponse
from .local_response import LocalSpaceTradersRespose
from .client_interface import SpaceTradersClient
import json
import os
import logging


class SpaceTradersCacheClient(SpaceTradersClient):
    def __init__(
        self,
        resources_folder_path="resources",
    ) -> None:
        # check if the resources folder exists
        # if not, create it
        folders = [
            resources_folder_path,
            os.path.join(resources_folder_path, "systems"),
            os.path.join(resources_folder_path, "waypoints"),
        ]
        self._path = resources_folder_path
        self.logger = logging.getLogger(__name__)
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

    token: str = None

    def _headers(self) -> dict:
        pass

    def update(self, update_obj):
        if isinstance(update_obj, Waypoint):
            if len(update_obj.traits) == 0:
                # this is a waypoint as viewed from a system
                # it should not override existing data (which may posess traits)
                return
            resp = try_save_json_file(
                update_obj.to_json(),
                self._path,
                "waypoints",
                f"{update_obj.symbol}.json",
            )
        elif isinstance(update_obj, System):
            # does it already exist? if so, don't update.
            try_save_json_file(
                update_obj.to_json(), self._path, "systems", f"{update_obj.symbol}.json"
            )

    def register(self, callsign, faction="COSMIC", email=None) -> SpaceTradersResponse:
        pass

    def systems_view_one(self, system_symbol: str) -> System or SpaceTradersResponse:
        source = try_load_json_file(self._path, "systems", f"{system_symbol}.json")
        if source:
            return System.from_json(source)
        return LocalSpaceTradersRespose(
            f"couldn't load {system_symbol} file from cache",
            0,
            0,
            "client_json_cache.systems_view_one",
        )

    def waypoints_view(
        self, system_symbol: str
    ) -> dict[str:Waypoint] or SpaceTradersResponse:
        # load the system object from the cache - it's got the list of waypoints
        return_obj = {}
        system = try_load_json_file(self._path, "systems", f"{system_symbol}.json")
        if system:
            system = System.from_json(system)
            return_obj = {w.symbol: w for w in system.waypoints}
        else:
            return LocalSpaceTradersRespose(
                f"couldn't load file from cache",
                0,
                0,
                "client_json_cache.waypoints_view",
            )

        for waypoint in system.waypoints:
            resp = self.waypoints_view_one(waypoint.symbol)
            if resp:
                return_obj[waypoint.symbol] = resp
        return return_obj

    def waypoints_view_one(self, waypoint_symbol) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.
            `force` (bool): Optional - Force a refresh of the waypoint. Defaults to False.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""
        pass
        source = try_load_json_file(self._path, "waypoints", f"{waypoint_symbol}.json")
        if source:
            waypoint = Waypoint.from_json(source)
            return waypoint

        return LocalSpaceTradersRespose(
            f"couldn't load file from cache", 0, 0, "client_json_cache.waypoints_view"
        )

    def find_waypoints_by_coords(
        self, system_symbol: str, x: int, y: int
    ) -> Waypoint or SpaceTradersResponse:
        waypoints = self.waypoints_view(system_symbol)
        if not waypoints:
            return waypoints
        resp = []
        for waypoint in waypoints.values():
            if waypoint.x == x and waypoint.y == y:
                resp.append(waypoint)
        return resp

    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        waypoints = self.waypoints_view(system_symbol)
        if not waypoints:
            return waypoints
        resp = []
        for waypoint in waypoints.values():
            waypoint: Waypoint
            if trait in [t.symbol for t in waypoint.traits]:
                resp.append(waypoint)
        return resp

        pass

    def find_waypoints_by_trait_one(
        self, system_symbol: str, trait: str
    ) -> Waypoint or SpaceTradersResponse:
        waypoints = self.waypoints_view(system_symbol)
        if not waypoints:
            return waypoints
        for waypoint in waypoints.values():
            waypoint: Waypoint
            if trait in [t.symbol for t in waypoint.traits]:
                return waypoint

    def find_waypoints_by_type(
        self, system_symbol, waypoint_type
    ) -> Waypoint or SpaceTradersResponse or None:
        waypoints = self.waypoints_view(system_symbol)
        if not waypoints:
            return waypoints
        return [w for w in waypoints.values() if w.type == waypoint_type]

    def find_waypoints_by_type_one(
        self, system_symbol, waypoint_type
    ) -> Waypoint or SpaceTradersResponse or None:
        waypoints = self.waypoints_view(system_symbol)
        if not waypoints:
            return waypoints
        for waypoint in waypoints.values():
            if waypoint.type == waypoint_type:
                return waypoint

    def surveys_mark_exhausted(self, survey_signature) -> None:
        """Removes a survey from any caching - called after an invalid survey response."""
        return dummy_response(__class__.__name__, "surveys_remove_one")
        pass

    def find_survey_best_deposit(
        self, waypoint_symbol: str, deposit_symbol: str
    ) -> Survey or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "find_survey_best_deposit")

    def find_survey_best(self, waypoint_symbol: str) -> Survey or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "find_survey_best_deposit")

    def agents_view_one(self, agent_symbol: str) -> "Agent" or SpaceTradersResponse:
        pass

    def set_current_agent(self, agent_symbol: str, token: str = None):
        self.current_agent_name = agent_symbol
        self.token = token

    def view_my_self(self) -> "Agent" or SpaceTradersResponse:
        pass

    def view_my_contracts(self) -> list["Contract"] or SpaceTradersResponse:
        pass

    def contracts_deliver(
        self, contract: "Contract", ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        pass

    def contracts_fulfill(self, contract: "Contract"):
        pass

    def ship_orbit(self, ship: "Ship"):
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        pass

    def ship_change_course(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/course"""
        pass

    def ship_warp(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/warp"""
        pass

    def ship_jump(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/jump"""
        pass

    def ship_move(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/navigate"""

        pass

    def ship_scan_ships(self, ship: "Ship") -> list["Ship"] or SpaceTradersResponse:
        """my/ships/:shipSymbol/scan"""

        pass

    def ship_siphon(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/siphon"""
        pass

    def ship_extract(self, ship: "Ship", survey: Survey = None) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""

        pass

    def ship_refine(self, ship: "Ship", trade_symbol) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refine"""

        pass

    def ship_dock(self, ship: "Ship"):
        """/my/ships/{shipSymbol}/dock"""
        pass

    def ship_refuel(self, ship: "Ship"):
        """/my/ships/{shipSymbol}/refuel"""
        pass

    def ship_sell(self, ship: "Ship", symbol: str, quantity: int):
        """/my/ships/{shipSymbol}/sell"""

        pass

    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity
    ) -> SpaceTradersResponse:
        pass

    def ship_survey(self, ship: "Ship") -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""

        pass

    def ship_transfer_cargo(self, ship: "Ship", trade_symbol, units, target_ship_name):
        """/my/ships/{shipSymbol}/transfer"""

        pass

    def ship_install_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/equip"""

        pass

    def ship_remove_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/remove"""

        pass

    def ship_jettison_cargo(
        self, ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/jettison"""

        pass

    def system_construction(self, wp: Waypoint) -> SpaceTradersResponse:
        """/systems/{systemSymbol}/waypoints/{waypointSymbol}/construct"""

        pass

    def system_market(
        self, system_symbol: str, waypoint_symbol: str
    ) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""

        pass

    def system_jumpgate(self, wp: Waypoint) -> "JumpGate" or SpaceTradersResponse:
        """/systems/{systemSymbol}/waypoints/{waypointSymbol}/jump-gate"""
        pass

    def ship_cooldown(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        return dummy_response(__class__.__name__, "ship_cooldown")

    def ship_negotiate(self, ship: "Ship") -> "Contract" or SpaceTradersResponse:
        "/my/ships/{shipSymbol}/negotiate/contract"
        return dummy_response(__class__.__name__, "ship_negotiate")

    def ship_patch_nav(self, ship: "Ship", flight_mode: str):
        "my/ships/:shipSymbol/nav"
        return dummy_response(__class__.__name__, "ship_patch_nav")

    def ships_purchase(
        self, ship_type: str, shipyard_waypoint: str
    ) -> tuple["Ship", "Agent"] or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "ships_purchase")

    def ships_view(self) -> dict[str:"Ship"] or SpaceTradersResponse:
        """/my/ships"""
        return dummy_response(__class__.__name__, "ships_view")

    def ships_view_one(self, symbol: str) -> "Ship" or SpaceTradersResponse:
        "/my/ships/{shipSymbol}"
        return dummy_response(__class__.__name__, "ships_view_one")

    def system_shipyard(self, wp: Waypoint) -> "Shipyard" or SpaceTradersResponse:
        """/systems/{systemSymbol}/shipyard"""
        return dummy_response(__class__.__name__, "system_shipyard")

    def systems_view_all(self) -> list[System] or SpaceTradersResponse:
        """/systems"""
        return dummy_response(__class__.__name__, "systems_view_all")

    def systems_view_twenty(
        self, page_number: int, force=False
    ) -> list["System"] or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "systems_view_twenty")


def dummy_response(class_name, method_name):
    return LocalSpaceTradersRespose(
        "Not implemented in this client", 0, 0, f"{class_name}.{method_name}"
    )


def try_load_json_file(*args) -> dict or None:
    """Try to load a json file from the given path. Returns None on failure."""
    try:
        with open(os.path.join(*args), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return LocalSpaceTradersRespose(
            f"File not found {args}", 0, 0, "client_json_cache.try_load_json_file"
        )
    except Exception as err:
        logging.getLogger(__name__).error(
            f"Exception {err} while loading json file {args}"
        )
        return LocalSpaceTradersRespose(
            f"Exception {err} while loading json file {args}",
            0,
            0,
            "client_json_cache.try_load_json_file",
        )


def try_save_json_file(data, *args) -> bool:
    """Try to save a json file to the given path. Returns False on failure."""
    try:
        with open(os.path.join(*args), "w+") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as err:
        logging.getLogger(__name__).error(
            f"Exception {err} while saving json file {args}"
        )
        return LocalSpaceTradersRespose(
            f"Exception {err} while saving json file {args}",
            0,
            0,
            "client_json_cache.try_save_json_file",
        )
