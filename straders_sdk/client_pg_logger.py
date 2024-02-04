from typing import Protocol, runtime_checkable
from .models import Waypoint, Survey, Market, Shipyard, Agent, ConstructionSite
from .ship import Ship
from .client_interface import SpaceTradersClient
import straders_sdk.utils as utils
from .responses import SpaceTradersResponse
from .pg_pieces.transactions import _upsert_transaction
from .pg_pieces.extractions import _upsert_extraction
from straders_sdk.utils import try_execute_select, try_execute_upsert, waypoint_slicer
import psycopg2
import uuid
import json
import logging
from .pg_connection_pool import PGConnectionPool as PG


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
        current_agent_symbol="",
        connection=None,
    ) -> None:
        self.token = token
        self.logger = logging.getLogger("PGLoggerClient")
        self.connection_pool = PG(db_user, db_pass, db_host, db_name, db_port)
        self._connection = connection
        self.session_id = str(uuid.uuid4())

        self.current_agent_name = current_agent_symbol
        utils.st_log_client = self

    @property
    def connection(self):
        if not self._connection:
            self._connection = self.connection_pool.get_connection()
        if not self._connection:
            return None
        if self._connection.closed:
            self.connection_pool.return_connection(self._connection)
            self._connection = self.connection_pool.get_connection()
        return self._connection

    def release_connection(self):
        if self._connection:
            self.connection_pool.return_connection(self._connection)
            self._connection = None

    def log_beginning(
        self,
        behaviour_name: str,
        ship_name="GLOBAL",
        starting_credits=None,
        behaviour_params=None,
    ):
        self.log_beginorend_event(
            "BEGIN_BEHAVIOUR_SCRIPT",
            behaviour_name,
            ship_name,
            starting_credits,
            behaviour_params,
        )

    def set_current_agent(self, agent_symbol: str, token: str = None):
        self.current_agent_name = agent_symbol
        self.token = token

    def log_ending(
        self,
        behaviour_name: str,
        ship_name="GLOBAL",
        starting_credits=None,
        behaviour_params=None,
    ):
        self.log_beginorend_event(
            "END_BEHAVIOUR_SCRIPT",
            behaviour_name,
            ship_name,
            starting_credits,
            behaviour_params,
        )

    def log_beginorend_event(
        self,
        event_name,
        behaviour_name: str,
        ship_name="GLOBAL",
        starting_credits=None,
        behaviour_params=None,
    ):
        if behaviour_params is None:
            behaviour_params = {}
        behaviour_params["script_name"] = behaviour_name
        sql = """INSERT INTO public.logging( event_name, event_timestamp, agent_name, ship_symbol, session_id, endpoint_name, new_credits, status_code, error_code, event_params)
        values (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s) on conflict(ship_symbol, event_timestamp) do nothing;"""
        return try_execute_upsert(
            sql=sql,
            params=(
                event_name,
                self.current_agent_name,
                ship_name,
                self.session_id,
                None,
                starting_credits,
                0,
                0,
                json.dumps(behaviour_params),
            ),
        )

    def log_custom_event(
        self, event_name, ship_name, event_params={}
    ) -> SpaceTradersResponse:
        sql = """INSERT INTO public.logging( event_name, event_timestamp, agent_name, ship_symbol, session_id, endpoint_name, new_credits, status_code, error_code, event_params)
        values (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s) on conflict(ship_symbol, event_timestamp) do nothing;"""
        return try_execute_upsert(
            sql=sql,
            params=(
                event_name,
                self.current_agent_name,
                ship_name,
                self.session_id,
                None,
                None,
                0,
                0,
                json.dumps(event_params),
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
        priority = None
        if response_obj is not None:
            if isinstance(response_obj, SpaceTradersResponse):
                status_code = response_obj.status_code
                error_code = response_obj.error_code
                priority = response_obj.request_proirity
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
	event_name, event_timestamp, agent_name, ship_symbol, session_id, endpoint_name, new_credits, status_code, error_code, event_params, duration_seconds, event_priority)
	VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on conflict (event_timestamp, ship_symbol) do nothing;"""

        resp = try_execute_upsert(
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
                priority,
            ),
            self.connection,
        )
        # if not resp:
        #    logging.error("Couldn't log event %s because %s", event_name, resp.error)
        # else:
        #    logging.debug("Logged event %s - %s", event_name, status_code)
        return resp

    def update(self, update_obj: SpaceTradersResponse):
        if isinstance(update_obj, SpaceTradersResponse):
            update_obj = update_obj.data
        if isinstance(update_obj, dict):
            if "transaction" in update_obj:
                _upsert_transaction(
                    update_obj["transaction"], self.session_id, self.connection
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
        self.log_event(
            "agents_view_one", "GLOBAL", endpoint, response, duration_seconds=duration
        )

    def view_my_self(
        self, response=None, duration: float = None
    ) -> "Agent" or SpaceTradersResponse:
        url = _url("my/agent")
        self.log_event(
            "view_my_self", "GLOBAL", url, response, duration_seconds=duration
        )

    def view_my_contracts(
        self, response=None, duration: float = None
    ) -> list["Contract"] or SpaceTradersResponse:
        url = _url("my/contracts")
        self.log_event(
            "view_my_contracts", "GLOBAL", url, response, duration_seconds=duration
        )

    def systems_view_twenty(
        self, page_number, response=None, duration: float = None
    ) -> dict[str:"System"] or SpaceTradersResponse:
        url = _url("systems")
        self.log_event(
            "systems_view_twenty", "GLOBAL", url, response, duration_seconds=duration
        )

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
        waypoint_symbol,
        response=None,
        duration: float = None,
    ) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""

        endpoint = f"systems/:system_symbol/waypoints/{waypoint_symbol}"
        self.log_event(
            "waypoints_view", "GLOBAL", endpoint, response, duration_seconds=duration
        )

    def find_waypoints_by_coords(
        self, system_symbol: str, x: int, y: int
    ) -> Waypoint or SpaceTradersResponse:
        # don't log anything, not an API call
        pass

    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str, resp=None, duration: float = None
    ) -> list[Waypoint] or SpaceTradersResponse:
        # don't log anything, not an API call
        pass

    def find_waypoints_by_type(
        self, system_wp: str, waypoint_type: str
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
        url = _url("my/ships/:ship_name/orbit")
        self.log_event(
            "ship_orbit", ship.name, url, response, duration_seconds=duration
        )
        pass

    def ship_patch_nav(
        self, ship: "Ship", flight_mode: str, response=None, duration: float = None
    ):
        """my/ships/:shipSymbol/course"""
        url = _url("my/ships/:ship_name/navigate")
        event_params = {"flight_mode": flight_mode}
        self.log_event(
            "ship_change_flight_mode",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )

    def ship_scan_waypoints(self, ship: "Ship", response=None, duration: float = None):
        url = _url("my/ships/:ship_name/scan/waypoints")
        self.log_event(
            "ship_scan_waypoints", ship.name, url, response, duration_seconds=duration
        )

    def ship_scan_ships(
        self, ship: "Ship", response=None, duration: float = None
    ) -> list["Ship"] or SpaceTradersResponse:
        url = _url("my/ships/:ship_name/scan-nearby-ships")
        self.log_event(
            "ship_scan_ships", ship.name, url, response, duration_seconds=duration
        )

    def ship_move(
        self,
        ship: "Ship",
        dest_waypoint_symbol: str,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/navigate"""
        url = _url("my/ships/:ship_name/navigate")
        event_params = {"dest_waypoint_symbol": dest_waypoint_symbol}
        self.log_event(
            "ship_move",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )

    def ship_create_chart(self, ship: "Ship", response=None, duration: float = None):
        """my/ships/:shipSymbol/chart"""
        url = _url("my/ships/:ship_name/chart")
        event_parms = {"charted_waypoint_symbol": ship.nav.waypoint_symbol}
        self.log_event(
            "ship_create_chart",
            ship.name,
            url,
            response,
            event_parms,
            duration_seconds=duration,
        )

    def ship_warp(
        self,
        ship: "Ship",
        dest_waypoint_symbol: str,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/warp"""
        url = _url("my/ships/:ship_name/warp")
        event_params = {
            "destination_waypoint": dest_waypoint_symbol,
            "destination_system": waypoint_slicer(dest_waypoint_symbol),
        }
        self.log_event(
            "ship_warp",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )

    def ship_jump(
        self,
        ship: "Ship",
        dest_waypoint_symbol: str,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/jump"""
        url = _url("my/ships/:ship_name/jump")
        event_params = {"dest_waypoint_symbol": dest_waypoint_symbol}
        self.log_event(
            "ship_jump",
            ship.name,
            url,
            response,
            event_params,
            duration_seconds=duration,
        )

    def surveys_mark_exhausted(self, survey_signature, ship_symbol: str = None) -> None:
        """Removes a survey from any caching - called after an invalid survey response."""
        self.log_event(
            "survey_exhausted",
            ship_symbol or "GLOBAL",
            "client.surveys_mark_exhausted",
            None,
            {"survey_id": survey_signature},
            0,
        )

    def ship_siphon(self, ship: "Ship", response=None, duration: float = None):
        url = _url("my/ships/:ship_name/siphon")
        siphon = response.data.get("siphon", {})
        siphon_yield = siphon.get("yield", {})
        event_params = None
        if siphon_yield.get("symbol"):
            event_params = {
                "trade_symbol": siphon_yield.get("symbol"),
                "units": siphon_yield["units"],
            }
            _upsert_extraction(
                siphon, self.session_id, ship.nav.waypoint_symbol, None, self.connection
            )
        self.log_event(
            "ship_siphon",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params=event_params,
        )

    def ship_extract(
        self, ship: "Ship", survey: Survey = None, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""
        url = _url("my/ships/:ship_name/extract")
        extraction = response.data.get("extraction", {})
        mining_yield = extraction.get("yield", {})
        event_params = {"extraction_waypoint": ship.nav.waypoint_symbol}
        if mining_yield.get("symbol"):
            event_params["trade_symbol"] = mining_yield.get("symbol")
            event_params["units"] = mining_yield["units"]
            _upsert_extraction(
                extraction,
                self.session_id,
                ship.nav.waypoint_symbol,
                survey.signature if survey is not None else None,
                self.connection,
            )
        response: SpaceTradersResponse

        self.log_event(
            "ship_extract",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params=event_params,
        )

    def ship_refine(
        self, ship: "Ship", trade_symbol, response=None, duration: float = None
    ):
        """/my/ships/{shipSymbol}/refine"""
        url = _url("my/ships/:ship_name/refine")
        self.log_event(
            "ship_refine", ship.name, url, response, duration_seconds=duration
        )

    def ship_dock(
        self, ship: "Ship", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/dock"""
        url = _url("my/ships/:ship_name/dock")
        self.log_event("ship_dock", ship.name, url, response, duration_seconds=duration)

    def ship_refuel(
        self, ship: "Ship", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refuel"""
        url = _url("my/ships/:ship_name/refuel")
        self.log_event(
            "ship_refuel", ship.name, url, response, duration_seconds=duration
        )

    def ship_sell(
        self,
        ship: "Ship",
        symbol: str,
        quantity: int,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""

        url = _url("my/ships/:ship_name/sell")
        params = None
        if response:
            params = {"trade_symbol": symbol, "units": quantity}

        self.log_event(
            "ship_sell",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params=params,
        )
        self.update(response)

    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        url = _url("my/ships/:ship_name/purchase")
        event_params = {"trade_symbol": symbol, "units": quantity}
        self.log_event(
            "ship_purchase_cargo",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params=event_params,
        )
        self.update(response)

    def ship_survey(
        self, ship: "ship", response=None, duration: float = None
    ) -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""
        url = _url("my/ships/:ship_name/survey")
        self.log_event(
            "ship_survey", ship.name, url, response, duration_seconds=duration
        )

    def ship_transfer_cargo(
        self,
        ship: "Ship",
        trade_symbol,
        units,
        target_ship_name,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        url = _url("my/ships/:ship_name/transfer")
        self.log_event(
            "ship_transfer_cargo",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params={"trade_symbol": trade_symbol, "units": units},
        )

        """/my/ships/{shipSymbol}/transfer"""

    def ship_install_mount(
        self, ship: "Ship", mount_symbol: str, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/equip"""
        url = _url("my/ships/:ship_name/equip")
        self.log_event(
            "ship_install_mount",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params={"installed_mount_symbol": mount_symbol},
        )

    def ship_remove_mount(
        self, ship: "Ship", mount_symbol: str, response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/remove"""
        url = _url("my/ships/:ship_name/mounts/remove")
        self.log_event(
            "ship_remove_mount",
            ship.name,
            url,
            response,
            duration_seconds=duration,
            event_params={"removed_mount_symbol": mount_symbol},
        )

    def ship_jettison_cargo(
        self,
        ship: "Ship",
        trade_symbol: str,
        units: int,
        response=None,
        duration: float = None,
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/jettison"""
        url = _url("my/ships/:ship_symbol/jettison")
        self.log_event(
            "ship_jettison_cargo", ship.name, url, response, duration_seconds=duration
        )

    def system_construction(
        self, wp: Waypoint, response=None, duration: float = None
    ) -> ConstructionSite or SpaceTradersResponse:
        """/systems/{symbol}/waypoints/{waypointSymbol}/construction}"""
        url = _url("systems/:system_symbol/waypoints/:waypoint_symbol/construction")
        self.log_event(
            "system_construction", "GLOBAL", url, response, duration_seconds=duration
        )

    def construction_supply(
        self, wp: Waypoint, ship: "Ship", trade_symbol, quantity, response, duration
    ):
        # put this down with the contracts stuff
        pass

    def system_market(
        self,
        wp: Waypoint,
        response=None,
        duration: float = None,
    ) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""
        url = _url("game/systems/:system_symbol/marketplace")
        self.log_event(
            "system_market", "GLOBAL", url, response, duration_seconds=duration
        )

    def systems_view_all(
        self, response=None, duration: float = None
    ) -> dict[str:"System"] or SpaceTradersResponse:
        """/systems"""
        url = _url("game/systems")
        self.log_event(
            "systems_list_all", "GLOBAL", url, response, duration_seconds=duration
        )

    def systems_view_one(
        self, system_symbol: str, response=None, duration: float = None
    ) -> "System" or SpaceTradersResponse:
        url = _url("/systems/:system_symbol")
        self.log_event(
            "systems_view_one", "GLOBAL", url, response, duration_seconds=duration
        )

    def system_shipyard(
        self, waypoint: Waypoint, response=None, duration: float = None
    ) -> Shipyard or SpaceTradersResponse:
        """/game/locations/{symbol}/shipyard"""
        url = _url("game/locations/:waypoint_symbol/shipyard")
        self.log_event(
            "system_shipyard", "GLOBAL", url, response, duration_seconds=duration
        )

    def system_jumpgate(
        self, wp: Waypoint, response=None, duration: float = None
    ) -> "JumpGate" or SpaceTradersResponse:
        """/game/systems/{symbol}/jumpgate"""
        url = _url("game/systems/:waypoint_symbol/jumpgate")
        self.log_event(
            "system_jumpgate", "GLOBAL", url, response, duration_seconds=duration
        )

    def ship_negotiate(
        self, ship: "ship", response=None, duration: float = None
    ) -> "Contract" or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/negotiate/contract"""
        url = _url("my/ships/:ship_name/negotiate/contract")

        self.log_event(
            "ship_negotiate", ship.name, url, response, duration_seconds=duration
        )

    def ship_cooldown(
        self, ship: "ship", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        url = _url("my/ships/:ship_name/cooldown")
        self.log_event(
            "ship_cooldown", ship.name, url, response, duration_seconds=duration
        )

    def ships_view(
        self, response=None, duration: float = None
    ) -> list["Ship"] or SpaceTradersResponse:
        """/my/ships"""
        url = _url("my/ships")
        self.log_event("ships_view", "GLOBAL", url, response, duration_seconds=duration)

    def ships_view_one(
        self, ship_symbol: str, response=None, duration: float = None
    ) -> "Ship" or SpaceTradersResponse:
        url = _url("my/ships/:ship_name")
        self.log_event(
            "ships_view_one", ship_symbol, url, response, duration_seconds=duration
        )

    def ships_purchase(
        self,
        ship_type: str,
        shipyard_waypoint: str,
        response=None,
        duration: float = None,
    ) -> tuple["Ship", "Agent"] or SpaceTradersResponse:
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
        url = _url("my/ships/:ship_name/deliver")
        self.log_event(
            "contracts_deliver", ship.name, url, response, duration_seconds=duration
        )

    def contracts_fulfill(
        self, contract: "Contract", response=None, duration: float = None
    ) -> SpaceTradersResponse:
        url = _url("my/contracts/:contract_id/fulfill")
        self.log_event(
            "contracts_fulfill", "GLOBAL", url, response, duration_seconds=duration
        )

    def log_429(self, url, response: SpaceTradersResponse):
        self.log_event("429", "GLOBAL", url, response)


def _url(endpoint: str) -> str:
    # purely exists to make copy/pasting between the api client and this file faster.
    return endpoint
