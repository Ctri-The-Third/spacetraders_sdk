from typing import Protocol, runtime_checkable
from .models import Waypoint, Survey, Market, Shipyard, Agent
from .ship import Ship
from .client_interface import SpaceTradersClient
import straders_sdk.utils as utils
from .responses import SpaceTradersResponse
from .pg_pieces.transactions import _upsert_transaction
from straders_sdk.utils import try_execute_select, try_execute_upsert
import psycopg2
import uuid
import json
import logging


class SpaceTradersPostgresLoggerClient(SpaceTradersClient):
    token: str = None

    def __init__(
        self,
        token,
        db_host,
        db_port,
        db_name,
        db_user,
        db_pass,
        current_agent_name="",
        connection=None,
    ) -> None:
        self.token = token
        self._connection = connection
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.logger = logging.getLogger("PGLoggerClient")
        if not self.connection:
            self.connection = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_pass,
            )
            self.connection.autocommit = True
        self.session_id = str(uuid.uuid4())

        self.current_agent_name = current_agent_name
        utils.st_log_client = self

    pass

    @property
    def connection(self):
        if self._connection is None or self._connection.closed > 0:
            self._connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass,
            )
            # self.logger.warning("Reconnected to database")
        return self._connection

    def log_beginning(
        self, behaviour_name: str, ship_name="GLOBAL", starting_credits=None
    ):
        self.log_custom_event(
            "BEGIN_BEHAVIOUR_SCRIPT", behaviour_name, ship_name, starting_credits
        )

    def log_ending(
        self, behaviour_name: str, ship_name="GLOBAL", starting_credits=None
    ):
        self.log_custom_event(
            "END_BEHAVIOUR_SCRIPT", behaviour_name, ship_name, starting_credits
        )

    def log_custom_event(
        self, event_name, behaviour_name: str, ship_name="GLOBAL", starting_credits=None
    ):
        sql = """INSERT INTO public.logging( event_name, event_timestamp, agent_name, ship_symbol, session_id, endpoint_name, new_credits, status_code, error_code, event_params)
        values (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s) on conflict(ship_symbol, event_timestamp) do nothing;"""
        return try_execute_upsert(
            self.connection,
            sql,
            (
                event_name,
                self.current_agent_name,
                ship_name,
                self.session_id,
                None,
                starting_credits,
                0,
                0,
                json.dumps({"script_name": behaviour_name}),
            ),
        )

    def log_event(
        self,
        event_name,
        ship_name,
        endpoint_name: str = None,
        response_obj=None,
        event_params={},
        duration_seconds: float = None,
    ) -> dict:
        error_code = 0
        status_code = 0
        new_credits = None
        connection = self.connection
        if response_obj is not None:
            if isinstance(response_obj, SpaceTradersResponse):
                status_code = response_obj.status_code
                error_code = response_obj.error_code
                credits = (
                    response_obj.response_json.get("data", {})
                    .get("agent", {})
                    .get("credits", None)
                )
                if credits:
                    new_credits = credits

            elif isinstance(response_obj, (Ship, Waypoint, Market, Shipyard)):
                status_code = 200

        if isinstance(ship_name, Ship):
            ship_name = ship_name.name
        sql = """INSERT INTO public.logging(
	event_name, event_timestamp, agent_name, ship_symbol, session_id, endpoint_name, new_credits, status_code, error_code, event_params, duration_seconds)
	VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s) on conflict (event_timestamp, ship_symbol) do nothing;"""

        return try_execute_upsert(
            connection,
            sql,
            (
                event_name,
                self.current_agent_name,
                ship_name,
                self.session_id,
                endpoint_name,
                new_credits,
                status_code,
                error_code,
                json.dumps(event_params),
                duration_seconds,
            ),
        )

        pass

    def update(self, update_obj: SpaceTradersResponse):
        if isinstance(update_obj, SpaceTradersResponse):
            update_obj = update_obj.data
        if isinstance(update_obj, dict):
            if "transaction" in update_obj:
                _upsert_transaction(
                    self.connection, update_obj["transaction"], self.session_id
                )
        return

    def register(
        self,
        callsign,
        faction="COSMIC",
        email=None,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        endpoint = "register"

        self.log_event("register", "GLOBAL", endpoint, response)

    def agents_view_one(
        self, agent_symbol: str, response=None, duration: float = None
    ) -> "Agent" or SpaceTradersResponse:
        endpoint = f"/agents/{agent_symbol}"
        self.log_event("agents_view_one", "GLOBAL", endpoint, response)

    def view_my_self(
        self, response=None, duration: float = None
    ) -> "Agent" or SpaceTradersResponse:
        url = _url("my/agent")
        self.log_event("view_my_self", "GLOBAL", url, response)

    def view_my_contracts(
        self, response=None, duration: float = None
    ) -> list["Contract"] or SpaceTradersResponse:
        url = _url("my/contracts")
        self.log_event("view_my_contracts", "GLOBAL", url, response)

    def systems_view_twenty(
        self, page_number, force=False, response=None, duration: float = None
    ) -> dict[str:"System"] or SpaceTradersResponse:
        url = _url("systems")
        self.log_event("systems_view_twenty", "GLOBAL", url, response)

    def waypoints_view(
        self, system_symbol: str, response=None, duration: float = None
    ) -> dict[str:list] or SpaceTradersResponse:
        """view all waypoints in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoints in.

        Returns:
            Either a dict of Waypoint objects or a SpaceTradersResponse object on failure.
        """
        endpoint = f"systems/:system_symbol/waypoints/"
        self.log_event(
            "waypoints_view", "GLOBAL", endpoint, response, duration_seconds=duration
        )

    def waypoints_view_one(
        self,
        system_symbol,
        waypoint_symbol,
        force=False,
        response=None,
        duration: float = None,
    ) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.
            `force` (bool): Optional - Force a refresh of the waypoint. Defaults to False.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""

        endpoint = f"systems/:system_symbol/waypoints/{waypoint_symbol}"
        self.log_event(
            "waypoints_view", "GLOBAL", endpoint, response, duration_seconds=duration
        )

        pass

    def find_waypoint_by_coords(
        self, system_symbol: str, x: int, y: int
    ) -> Waypoint or SpaceTradersResponse:
        # don't log anything, not an API call
        pass

    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str, resp=None, duration: float = None
    ) -> list[Waypoint] or SpaceTradersResponse:
        # don't log anything, not an API call

        pass

    def find_waypoints_by_trait_one(
        self, system_symbol: str, trait: str
    ) -> Waypoint or SpaceTradersResponse:
        # don't log anything, not an API call

        pass

    def find_waypoints_by_type_one(
        self, system_wp, waypoint_type
    ) -> Waypoint or SpaceTradersResponse:
        # don't log anything, not an API call
        pass

    def find_survey_best_deposit(
        self, waypoint_symbol: str, deposit_symbol: str
    ) -> Survey or SpaceTradersResponse:
        # don't log anything, not an API call
        pass

    def find_survey_best(self, waypoint_symbol: str) -> Survey or SpaceTradersResponse:
        # don't log anything, not an API call
        pass

    def ship_orbit(
        self, ship, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        url = _url(f"my/ships/:ship_name/orbit")
        self.log_event(
            "ship_orbit", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_patch_nav(
        self, ship: "Ship", flight_mode: str, response=None, duration: float = None
    ):
        """my/ships/:shipSymbol/course"""
        url = _url(f"my/ships/:ship_name/navigate")
        event_params = {"flight_mode": flight_mode}
        self.log_event(
            "ship_change_flight_mode",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )
        pass

    def ship_move(
        self,
        ship: "Ship",
        dest_waypoint_symbol: str,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/navigate"""
        url = _url(f"my/ships/:ship_name/navigate")
        event_params = {"dest_waypoint_symbol": dest_waypoint_symbol}
        self.log_event(
            "ship_move",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )

        pass

    def ship_jump(
        self,
        ship: "Ship",
        dest_waypoint_symbol: str,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/jump"""
        url = _url(f"my/ships/:ship_name/jump")
        event_params = {"dest_waypoint_symbol": dest_waypoint_symbol}
        self.log_event(
            "ship_jump",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )

        pass

    def surveys_remove_one(self, survey_signature) -> None:
        """Removes a survey from any caching - called after an invalid survey response."""
        pass

    def ship_extract(
        self, ship: "Ship", survey: Survey = None, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""
        url = _url(f"my/ships/:ship_name/extract")
        mining_yield = response.data.get("extraction", {}).get("yield", {})
        event_params = None
        if mining_yield.get("symbol"):
            event_params = {
                "trade_symbol": mining_yield.get("symbol"),
                "units": mining_yield["units"],
            }
        self.log_event(
            "ship_extract",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params=event_params,
        )
        pass

    def ship_refine(
        self, ship: "Ship", trade_symbol, response=None, duration: float = None
    ):
        """/my/ships/{shipSymbol}/refine"""
        url = _url(f"my/ships/:ship_name/refine")
        self.log_event(
            "ship_refine", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_dock(
        self, ship: "Ship", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/dock"""
        url = _url(f"my/ships/:ship_name/dock")
        self.log_event("ship_dock", ship.name, url, response, duration_seconds=duration)
        pass

    def ship_refuel(
        self, ship: "Ship", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refuel"""
        url = _url(f"my/ships/:ship_name/refuel")
        self.log_event(
            "ship_refuel", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_sell(
        self,
        ship: "Ship",
        symbol: str,
        quantity: int,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""

        url = _url(f"my/ships/:ship_name/sell")
        self.log_event("ship_sell", ship.name, url, response, duration_seconds=duration)
        self.update(response)

        pass

    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        url = _url(f"my/ships/:ship_name/purchase")
        self.log_event(
            "ship_purchase_cargo", ship.name, url, response, duration_seconds=duration
        )
        self.update(response)

    def ship_survey(
        self, ship: "ship", response=None, duration: float = None
    ) -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""
        url = _url(f"my/ships/:ship_name/survey")
        self.log_event(
            "ship_survey", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_transfer_cargo(
        self,
        ship: "Ship",
        trade_symbol,
        units,
        target_ship_name,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        url = _url(f"my/ships/:ship_name/transfer")
        self.log_event(
            "ship_transfer_cargo", ship.name, url, response, duration_seconds=duration
        )

        """/my/ships/{shipSymbol}/transfer"""

        pass

    def ship_install_mount(
        self, ship: "Ship", mount_symbol: str, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/equip"""
        url = _url(f"my/ships/:ship_name/equip")
        self.log_event(
            "ship_install_mount", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_jettison_cargo(
        self,
        ship: "Ship",
        trade_symbol: str,
        units: int,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/jettison"""
        url = _url(f"my/ships/:ship_symbol/jettison")
        self.log_event(
            "ship_jettison_cargo", ship.name, url, response, duration_seconds=duration
        )
        pass

    def system_market(
        self,
        wp: Waypoint,
        response=None,
        duration: float = None,
    ) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""
        url = _url(f"game/systems/:system_symbol/marketplace")
        self.log_event(
            "system_market", "GLOBAL", url, response, duration_seconds=duration
        )
        pass

    def systems_view_all(
        self, response=None, duration: float = None
    ) -> dict[str:"System"] or SpaceTradersResponse:
        """/systems"""
        url = _url(f"game/systems")
        self.log_event(
            "systems_list_all", "GLOBAL", url, response, duration_seconds=duration
        )
        pass

    def systems_view_one(
        self, system_symbol: str, response=None, duration: float = None
    ) -> "System" or SpaceTradersResponse:
        url = _url(f"/systems/:system_symbol")
        self.log_event(
            "systems_view_one", "GLOBAL", url, response, duration_seconds=duration
        )

    def system_shipyard(
        self, waypoint: Waypoint, response=None, duration: float = None
    ) -> Shipyard or SpaceTradersResponse:
        """/game/locations/{symbol}/shipyard"""
        url = _url(f"game/locations/:waypoint_symbol/shipyard")
        self.log_event(
            "system_shipyard", "GLOBAL", url, response, duration_seconds=duration
        )

        pass

    def system_jumpgate(
        self, wp: Waypoint, force_update=False, response=None, duration: float = None
    ) -> "JumpGate" or SpaceTradersResponse:
        """/game/systems/{symbol}/jumpgate"""
        url = _url(f"game/systems/:waypoint_symbol/jumpgate")
        self.log_event(
            "system_jumpgate", "GLOBAL", url, response, duration_seconds=duration
        )
        pass

    def ship_negotiate(
        self, ship: "ship", response=None, duration: float = None
    ) -> "Contract" or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/negotiate/contract"""
        url = _url(f"my/ships/:ship_name/negotiate/contract")

        self.log_event(
            "ship_negotiate", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_cooldown(
        self, ship: "ship", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        url = _url(f"my/ships/:ship_name/cooldown")
        self.log_event(
            "ship_cooldown", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ships_view(
        self, response=None, duration: float = None
    ) -> list["Ship"] or SpaceTradersResponse:
        """/my/ships"""
        url = _url(f"my/ships")
        self.log_event("ships_view", "GLOBAL", url, response, duration_seconds=duration)

        pass

    def ships_view_one(
        self, ship_symbol: str, response=None, duration: float = None
    ) -> "Ship" or SpaceTradersResponse:
        url = _url(f"my/ships/:ship_name")
        self.log_event(
            "ships_view_one", ship_symbol, url, response, duration_seconds=duration
        )
        pass

    def ships_purchase(
        self,
        ship_type: str,
        shipyard_waypoint: str,
        response=None,
        duration: float = None,
    ) -> tuple["Ship", "Agent"] or SpaceTradersResponse:
        pass
        url = _url("my/ships")
        self.log_event(
            "ships_purchase", "GLOBAL", url, response, duration_seconds=duration
        )

    def contracts_deliver(
        self,
        contract: "Contract",
        ship: "Ship",
        trade_symbol: str,
        units: int,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        url = _url(f"my/ships/:ship_name/deliver")
        self.log_event(
            "contracts_deliver", ship.name, url, response, duration_seconds=duration
        )
        pass

    def contracts_fulfill(
        self, contract: "Contract", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        url = _url(f"my/contracts/:contract_id/fulfill")
        self.log_event(
            "contracts_fulfill", "GLOBAL", url, response, duration_seconds=duration
        )
        pass

    def log_429(self, url, response: SpaceTradersResponse):
        self.log_event("429", "GLOBAL", url, response)


def _url(endpoint: str) -> str:
    # purely exists to make copy/pasting between the api client and this file faster.
    return endpoint
