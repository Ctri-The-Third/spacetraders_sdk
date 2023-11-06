from typing import Protocol
from .models import Waypoint, Survey, Market
from .responses import SpaceTradersResponse


class SpaceTradersStubClient:
    token: str = None

    def _headers(self) -> dict:
        pass

    def update(self, update_obj):
        pass

    def register(self, callsign, faction="COSMIC", email=None) -> SpaceTradersResponse:
        pass

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

    def agents_view_one(self, agent_symbol: str) -> "Agent" or SpaceTradersResponse:
        pass

    def set_current_agent(self, agent_symbol: str, token: str = None):
        self.current_agent_name = agent_symbol
        self.token = token

    def view_my_self(self) -> "Agent" or SpaceTradersResponse:
        pass

    def view_my_contracts(self) -> list["Contract"] or SpaceTradersResponse:
        pass

    def waypoints_view_one(
        self, system_symbol, waypoint_symbol, force=False
    ) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.
            `force` (bool): Optional - Force a refresh of the waypoint. Defaults to False.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""
        pass

    def find_waypoint_by_coords(
        self, system_symbol: str, x: int, y: int
    ) -> Waypoint or SpaceTradersResponse:
        pass

    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        pass

    def find_waypoints_by_trait_one(
        self, system_symbol: str, trait: str
    ) -> Waypoint or SpaceTradersResponse:
        pass

    def find_waypoints_by_type(
        self, system_wp, waypoint_type
    ) -> Waypoint or SpaceTradersResponse or None:
        pass

    def ship_orbit(self, ship: "Ship"):
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        pass

    def ship_change_course(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/course"""
        pass

    def ship_move(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/navigate"""

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

    def system_market(
        self, system_symbol: str, waypoint_symbol: str
    ) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""

        pass

    def system_jumpgate(self, wp: Waypoint) -> "JumpGate" or SpaceTradersResponse:
        """/systems/{systemSymbol}/waypoints/{waypointSymbol}/jump-gate"""
        pass
