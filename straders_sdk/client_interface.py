from typing import Protocol, runtime_checkable
from .models_misc import Waypoint, Survey, Market, Shipyard, JumpGate, ConstructionSite
from .responses import SpaceTradersResponse
from abc import abstractmethod


class SpaceTradersInteractive(Protocol):
    token: str = None

    def __init__(self, token) -> None:
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def update(self, json_data: dict):
        pass


@runtime_checkable
class SpaceTradersClient(Protocol):
    token: str = None

    @abstractmethod
    def __init__(self, token, connection=None) -> None:
        pass

    @abstractmethod
    def update(self, update_obj):
        pass

    @abstractmethod
    def register(self, callsign, faction="COSMIC", email=None) -> SpaceTradersResponse:
        pass

    @abstractmethod
    def agents_view_one(self, agent_symbol: str) -> "Agent" or SpaceTradersResponse:
        pass

    @abstractmethod
    def set_current_agent(self, agent_symbol: str, token: str = None):
        pass

    @abstractmethod
    def view_my_self(self) -> "Agent" or SpaceTradersResponse:
        pass

    @abstractmethod
    def view_my_contracts(self) -> list["Contract"] or SpaceTradersResponse:
        pass

    def release_connection(self):
        """A method that instructs the SDK to release any applicable DB connections back to a connction pool in multi-threaded applications.
        does nothing if the client does not have database connectivity, or if the client does not support connection pooling.

        Useful if you've just enabled a long cooldown and have instructed the thread to sleep.
        """

    @abstractmethod
    def waypoints_view(
        self, system_symbol: str
    ) -> dict[str:list] or SpaceTradersResponse:
        """view all waypoints in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoints in.

        Returns:
            Either a dict of Waypoint objects or a SpaceTradersResponse object on failure.
        """
        pass

    @abstractmethod
    def waypoints_view_one(
        self, waypoint_symbol, force=False
    ) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.
            `force` (bool): Optional - Force a refresh of the waypoint. Defaults to False.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""
        pass

    @abstractmethod
    def find_waypoints_by_coords(
        self, system: str, x: int, y: int
    ) -> list[Waypoint] or SpaceTradersResponse:
        """find a waypoint by its coordinates. Only searches cached values.

        Args:
            `system` (str): The symbol of the system to search in.
            `x` (int): The x coordinate of the waypoint.
            `y` (int): The y coordinate of the waypoint.

        Returns:
            Either a Waypoint object or None if no matching waypoint is found.
        """

    @abstractmethod
    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_waypoints_by_trait_one(
        self, system_symbol: str, trait: str
    ) -> Waypoint or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_waypoints_by_type(
        self, system_wp: str, waypoint_type: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_waypoints_by_type_one(
        self, system_wp, waypoint_type
    ) -> Waypoint or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_survey_best_deposit(
        self, waypoint_symbol: str, deposit_symbol: str
    ) -> Survey or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_survey_best(self, waypoint_symbol: str) -> Survey or SpaceTradersResponse:
        pass

    @abstractmethod
    def surveys_mark_exhausted(self, survey_signature) -> None:
        """Removes a survey from any caching - called after an invalid survey response."""
        pass

    @abstractmethod
    def ship_orbit(self, ship: "Ship") -> SpaceTradersResponse:
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        pass

    @abstractmethod
    def ship_patch_nav(self, ship: "Ship", flight_mode: str):
        """my/ships/:shipSymbol/course"""
        pass

    @abstractmethod
    def ship_move(
        self, ship: "Ship", dest_waypoint_symbol: str
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/navigate"""

        pass

    def ship_create_chart(self, ship: "Ship"):
        """my/ships/:shipSymbol/chart"""

    @abstractmethod
    def ship_scan_ships(self, ship: "Ship") -> list["Ship"] or SpaceTradersResponse:
        """my/ships/:shipSymbol/scan"""

        pass

    @abstractmethod
    def ship_warp(
        self, ship: "Ship", dest_waypoint_symbol: str
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/warp"""

        pass

    @abstractmethod
    def ship_jump(self, ship, dest_symbol_string) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/jump"""

        pass

    @abstractmethod
    def ship_siphon(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/siphon"""

    @abstractmethod
    def ship_extract(self, ship: "Ship", survey: Survey = None) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""

        pass

    @abstractmethod
    def ship_refine(self, ship: "Ship", trade_symbol: str) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refine"""

        pass

    @abstractmethod
    def ship_dock(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/dock"""
        pass

    @abstractmethod
    def ship_refuel(
        self, ship: "Ship", from_cargo: bool = False
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refuel"""
        pass

    @abstractmethod
    def ship_sell(
        self, ship: "Ship", symbol: str, quantity: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""

        pass

    @abstractmethod
    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/purchase"""
        pass

    @abstractmethod
    def ship_survey(self, ship: "Ship") -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""

        pass

    @abstractmethod
    def ship_transfer_cargo(
        self, ship: "Ship", trade_symbol, units, target_ship_name
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/transfer"""

    @abstractmethod
    def ship_install_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/install"""

        pass

    @abstractmethod
    def ship_remove_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/remove"""

        pass

    @abstractmethod
    def ship_jettison_cargo(
        self, ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/jettison"""

        pass

    @abstractmethod
    def system_construction(
        self, wp: Waypoint
    ) -> ConstructionSite or SpaceTradersResponse:
        """/systems/{symbol}/waypoints/{waypointSymbol}/construction}"""

        pass

    @abstractmethod
    def system_market(self, wp: Waypoint) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""

        pass

    @abstractmethod
    def system_jumpgate(self, wp: Waypoint) -> JumpGate or SpaceTradersResponse:
        """/systems/{systemSymbol}/waypoints/{waypointSymbol}/jump-gate"""
        pass

    @abstractmethod
    def systems_view_twenty(
        self, page_number: int, force=False
    ) -> dict[str:"System"] or SpaceTradersResponse:
        pass

    @abstractmethod
    def systems_view_all(self) -> dict[str:"System"] or SpaceTradersResponse:
        """/game/systems"""

        pass

    @abstractmethod
    def systems_view_one(self, symbol: str) -> "System" or SpaceTradersResponse:
        """/game/systems/{symbol}"""

        pass

    @abstractmethod
    def system_shipyard(self, waypoint: Waypoint) -> Shipyard or SpaceTradersResponse:
        """/game/locations/{symbol}/shipyard"""

        pass

    @abstractmethod
    def ship_negotiate(self, ship: "Ship") -> "Contract" or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/negotiate/contract"""
        pass

    @abstractmethod
    def ship_cooldown(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        pass

    @abstractmethod
    def ships_view(self) -> list["Ship"] or SpaceTradersResponse:
        """/my/ships"""

        pass

    @abstractmethod
    def ships_view_one(self, symbol: str) -> "Ship" or SpaceTradersResponse:
        pass

    @abstractmethod
    def ships_purchase(
        self, ship_type: str, shipyard_waypoint: str
    ) -> tuple["Ship", "Agent"] or SpaceTradersResponse:
        pass

    @abstractmethod
    def contracts_deliver(
        self, contract: "Contract", ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        pass

    @abstractmethod
    def contracts_fulfill(self, contract: "Contract") -> SpaceTradersResponse:
        pass
