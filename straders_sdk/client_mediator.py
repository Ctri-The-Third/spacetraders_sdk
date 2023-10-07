from .utils import get_and_validate, get_and_validate_paginated, post_and_validate, _url
from .utils import ApiConfig, _log_response
from .client_interface import SpaceTradersInteractive, SpaceTradersClient

from .responses import SpaceTradersResponse
from .local_response import LocalSpaceTradersRespose
from .contracts import Contract
from .models import (
    Waypoint,
    ShipyardShip,
    GameStatus,
    Agent,
    Survey,
    ShipNav,
    Market,
    JumpGate,
)
import psycopg2
from .models import Shipyard, System
from .ship import Ship
from .client_api import SpaceTradersApiClient
from .client_stub import SpaceTradersStubClient
from .client_postgres import SpaceTradersPostgresClient
from .client_pg_logger import SpaceTradersPostgresLoggerClient
from threading import Lock
import logging

# Attempted relative import beyond top-level packagePylintE0402:relative-beyond-top-level
from datetime import datetime


class SpaceTradersMediatorClient(SpaceTradersClient):
    """SpaceTraders API client, with in-memory caching, and DB lookup."""

    api_client: SpaceTradersClient
    db_client: SpaceTradersClient
    current_agent: Agent
    ships: dict[str, Ship]
    waypoints: dict[str, Waypoint]
    system_waypoints: dict[str : list[Waypoint]]

    def __init__(
        self,
        token=None,
        base_url=None,
        version=None,
        db_host=None,
        db_name=None,
        db_user=None,
        db_pass=None,
        db_port=None,
        current_agent_symbol=None,
        session=None,
        connection=None,
    ) -> None:
        self.logger = logging.getLogger(__name__)

        self.token = token
        self.current_agent = current_agent_symbol
        if db_host and db_name and db_user and db_pass:
            if not connection:
                connection = psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    database=db_name,
                    user=db_user,
                    password=db_pass,
                    application_name="unspecified ST client",
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=3,  # connection terminates after 30 seconds of silence
                )
                connection.autocommit = True

            self.db_client = SpaceTradersPostgresClient(
                db_host=db_host,
                db_name=db_name,
                db_user=db_user,
                db_pass=db_pass,
                db_port=db_port,
                current_agent_symbol=current_agent_symbol,
                connection=connection,
            )
            self.logging_client = SpaceTradersPostgresLoggerClient(
                db_host=db_host,
                db_port=db_port,
                db_name=db_name,
                db_user=db_user,
                db_pass=db_pass,
                token=token,
                connection=connection,
            )
        else:
            self.db_client = SpaceTradersStubClient()
            self.logging_client = SpaceTradersStubClient()
            self.logger.warning(
                "Couldn't enable DB client, missing info, no logs will be taken"
            )
            self.logger.debug(
                "passed in values were: %s, %s, %s, %s",
                db_host,
                db_name,
                db_user,
                db_pass,
            )
        self.api_client = SpaceTradersApiClient(
            token=token, base_url=base_url, version=version, session=session
        )
        self.config = ApiConfig(
            base_url=base_url, version=version
        )  # set up the global config for other things to use.
        self.ships = {}
        self.waypoints = {}
        self.contracts = {}
        self.system_waypoints = {}
        self.current_agent = None
        self.current_agent_symbol = current_agent_symbol
        self.surveys: dict[str:Survey] = {}
        self._lock = Lock()

    def game_status(self) -> GameStatus:
        """Get the status of the SpaceTraders game server.

        Args:
            None"""

        url = _url("")
        resp = get_and_validate(url)

        return GameStatus(resp.response_json)

    def register(self, callsign, faction="COSMIC", email=None) -> SpaceTradersResponse:
        """Register a new agent.

        Args:
            `callsign` (str): The callsign of the agent
            `faction` (str): The faction the agent will be a part of. Defaults to "COSMIC"
            `email` (str): The email of the agent. Optional. Used for managing tokens in the SpaceTraders UI.
        """
        resp = self.api_client.register(callsign, faction, email)
        if resp:
            self.token = resp.data["token"]
            self.update(resp.data)
        return resp

    def agents_view_one(
        self, symbol: str, force=False
    ) -> Agent or SpaceTradersResponse:
        if not force:
            resp = self.db_client.agents_view_one(symbol)
            if resp:
                return resp
        start = datetime.now()
        resp = self.api_client.agents_view_one(symbol)
        if resp:
            self.logging_client.agents_view_one(
                resp, (datetime.now() - start).total_seconds()
            )
            self.update(resp)
        return resp

    def set_current_agent(self, agent_symbol: str, token: str = None):
        self.current_agent_symbol = agent_symbol
        self.token = token
        self.db_client.set_current_agent(agent_symbol, token)
        self.logging_client.set_current_agent(agent_symbol, token)
        self.api_client.set_current_agent(agent_symbol, token)

    def view_my_self(self, force=False) -> Agent or SpaceTradersResponse:
        """view the current agent, uses cached value unless forced.

        Args:
            `force` (bool): Optional - Force a refresh of the agent. Defaults to False.
        """

        # db handling of this should include MD5 hashing of the token for identification.
        if self.current_agent and not force:
            return self.current_agent

        if not force:
            resp = self.db_client.view_my_self()
            if resp:
                self.current_agent = resp
                self.current_agent_symbol = resp.symbol
                return resp
        start = datetime.now()
        resp = self.api_client.view_my_self()

        self.logging_client.view_my_self(resp, (datetime.now() - start).total_seconds())
        if resp:
            self.current_agent = resp
            self.current_agent_symbol = resp.symbol
            self.update(resp)
        return resp

    def ships_view(self, force=False) -> dict[str, Ship] or SpaceTradersResponse:
        """view the current ships the agent has, a dict that's accessible by ship symbol.
        uses cached values by default.

        Args:
            `force` (bool): Optional - Force a refresh of the ships. Defaults to False.
        """
        if not force:
            resp = self.db_client.ships_view()
            if resp:
                self.ships = self.ships | resp
                return resp
        start = datetime.now()
        resp = self.api_client.ships_view()
        self.logging_client.ships_view(resp, (datetime.now() - start).total_seconds())
        if resp:
            new_ships = resp
            self.ships = self.ships | new_ships
            for ship in self.ships.values():
                ship: Ship
                ship.dirty = True  # force a refresh of the ship into the DB
                self.db_client.update(ship)
            return new_ships
        return resp

    def ships_view_one(self, symbol: str, force=False):
        if not force and symbol in self.ships:
            resp = self.ships.get(symbol, None)
            if resp:
                return self.ships[symbol]

        if not force:
            resp = self.db_client.ships_view_one(symbol)
            if resp:
                resp: Ship
                self.ships[symbol] = resp
                return resp
        start = datetime.now()
        resp = self.api_client.ships_view_one(symbol)
        self.logging_client.ships_view_one(
            symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            resp: Ship
            resp.dirty = True
            self.ships[symbol] = resp
            self.db_client.update(resp)
        return resp

    def ships_purchase(
        self, ship_type: str or ShipyardShip, waypoint: str or Waypoint
    ) -> tuple[Ship, Agent] or SpaceTradersResponse:
        """purchase a ship from a given shipyard waypoint.

        Args:
            `waypoint` (str or Waypoint): The waypoint to purchase the ship from. Can be a waypoint symbol or a Waypoint object.
            `ship_type` (str or ShipyardShip): The type of ship to purchase. Can be a ship_type identifier or a ShipyardShip object.

            Returns:
                Either a Ship object or a SpaceTradersResponse object on failure."""
        start = datetime.now()
        resp = self.api_client.ships_purchase(ship_type, waypoint)
        self.logging_client.ships_purchase(
            ship_type, waypoint, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            self.update(resp[0])
            self.update(resp[1])

        return resp

    def view_my_contracts(self, force=False) -> list[Contract] or SpaceTradersResponse:
        """view the current contracts the agent has, uses cached values by default.

        Args:
            `force` (bool): Optional - Force a refresh of the contracts. Defaults to False.

        Returns:
            Either a dict of Contract objects or a SpaceTradersResponse object on failure.
        """
        if not force:
            resp = self.db_client.view_my_contracts()
            if resp:
                self.contracts = self.contracts | {c.id: c for c in resp}
                return resp
        start = datetime.now()
        resp = self.api_client.view_my_contracts()
        self.logging_client.view_my_contracts(
            resp, (datetime.now() - start).total_seconds()
        )
        if resp or (isinstance(resp, dict) and len(resp) == 0):
            for c in resp:
                self.update(c)
            self.contracts = self.contracts | {c.id: c for c in resp}
            return resp

    def contract_accept(self, contract_id) -> Contract or SpaceTradersResponse:
        """accept a contract

        Args:
            `contract_id` (str): The id of the contract to accept.

        Returns:
                Either a Contract object or a SpaceTradersResponse object on failure."""
        url = _url(f"my/contracts/{contract_id}/accept")
        resp = post_and_validate(url, headers=self._headers())

        if not resp:
            return resp
        new_contract = Contract.from_json(resp.data["contract"])
        self.contracts[new_contract.id] = new_contract
        self.update(new_contract)

        return new_contract

    def update(self, json_data):
        """Parses the json data from a response to update the agent, add a new survey, or add/update a new contract.

        This method is present on all Classes that can cache responses from the API."""
        if isinstance(json_data, SpaceTradersResponse):
            if json_data.data is not None:
                json_data = json_data.data
        if isinstance(json_data, dict):
            if "agent" in json_data:
                if self.current_agent is not None:
                    self.current_agent.update(json_data)
                    self.update(self.current_agent)
                else:
                    self.current_agent = Agent.from_json(json_data["agent"])
            if "surveys" in json_data:
                for survey in json_data["surveys"]:
                    surv = Survey.from_json(survey)
                    self.update(surv)
            if "contract" in json_data:
                contract = Contract.from_json(json_data["contract"])
                self.contracts[json_data["contract"]["id"]] = contract
                self.update(contract)
            if "nav" in json_data:
                pass  # this belongs to a ship, can't exist by itself. Call ship.update(json_data) instead, then do self.update(ship)
            if "cooldown" in json_data:
                pass  # this belongs to a ship, can't exist by itself. Call ship.update(json_data) instead
            # if "transaction" in json_data:
            #    self.logging_client.update(json_data)
        if isinstance(json_data, Survey):
            self.surveys[json_data.signature] = json_data
            self.db_client.update(json_data)
        if isinstance(json_data, Ship):
            self.ships[json_data.name] = json_data
            self.db_client.update(json_data)
        if isinstance(json_data, Waypoint):
            self.waypoints[json_data.symbol] = json_data
        if isinstance(json_data, Agent):
            self.current_agent = json_data
            self.db_client.update(json_data)
        if isinstance(json_data, Survey):
            self.surveys[json_data.signature] = json_data
            self.db_client.update(json_data)
        if isinstance(json_data, Contract):
            self.contracts[json_data.id] = json_data
            self.db_client.update(json_data)

    def waypoints_view_one(
        self, system_symbol, waypoint_symbol, force=False
    ) -> Waypoint or SpaceTradersResponse:
        # check self
        if waypoint_symbol in self.waypoints and not force:
            return self.waypoints[waypoint_symbol]

        # check db
        if not force:
            wayp = self.db_client.waypoints_view_one(system_symbol, waypoint_symbol)
            if wayp:
                self.update(wayp)
                return wayp
        # check api
        start = datetime.now()
        wayp = self.api_client.waypoints_view_one(system_symbol, waypoint_symbol)
        self.logging_client.waypoints_view_one(
            system_symbol,
            waypoint_symbol,
            wayp,
            (datetime.now() - start).total_seconds(),
        )
        if wayp:
            self.update(wayp)
            self.db_client.update(wayp)
            return wayp
        return wayp

    def waypoints_view(
        self, system_symbol: str, force=False
    ) -> dict[str:Waypoint] or SpaceTradersResponse:
        """view all waypoints in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoints in.

        Returns:
            Either a dict of Waypoint objects or a SpaceTradersResponse object on failure.
        """
        # check cache
        if not force and system_symbol in self.system_waypoints:
            return self.system_waypoints[system_symbol]

        if not force:
            new_wayps = self.db_client.waypoints_view(system_symbol)
            if new_wayps:
                for new_wayp in new_wayps.values():
                    self.update(new_wayp)
                return new_wayps
        start = datetime.now()
        new_wayps = self.api_client.waypoints_view(system_symbol)
        self.logging_client.waypoints_view(
            system_symbol, new_wayps, (datetime.now() - start).total_seconds()
        )
        if new_wayps:
            for new_wayp in new_wayps.values():
                self.db_client.update(new_wayp)
                self.update(new_wayp)
        return new_wayps

    def view_my_ships_one(
        self, ship_id: str, force=False
    ) -> Ship or SpaceTradersResponse:
        """view a single ship owned by the agent. Uses cached values by default.


        Args:
            `ship_id` (str): The id of the ship to view.
            `force` (bool): Optional - Force a refresh of the ship. Defaults to False.

        Returns:
            Either a Ship object or a SpaceTradersResponse object on failure."""
        self.logger.warning("USing depreciated method `view_my_ships_one`")
        return self.ships_view_one(ship_id, force)

    def systems_view_twenty(
        self, page_number, force=False
    ) -> dict[str:"System"] or SpaceTradersResponse:
        """View 20 systems at a time. No caching available for this method, as we can't guarantee a syncing between the order of the DB and the API."""

        start = datetime.now()
        resp = self.api_client.systems_view_twenty(
            page_number, (datetime.now() - start).total_seconds()
        )
        self.logging_client.systems_view_twenty(resp)

        if not resp:
            return resp
        if resp:
            for syst in resp:
                syst: System
                self.db_client.update(syst)
        return resp

    def systems_view_all(
        self, force=False
    ) -> dict[str:"System"] or SpaceTradersResponse:
        """/game/systems"""
        if not force:
            resp = self.db_client.systems_view_all()
            if resp:
                return resp

        start = datetime.now()
        resp = self.api_client.systems_view_all()
        self.logging_client.systems_view_all(
            resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            for syst in resp:
                syst: System
                self.db_client.update(syst)
            return {d.symbol: d for d in resp}

    def systems_view_one(
        self, system_symbol: str, force=False
    ) -> System or SpaceTradersResponse:
        """View a single system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to view.

        Returns:
            Either a System object or a SpaceTradersResponse object on failure.
        """
        if not force:
            resp = self.db_client.systems_view_one(system_symbol)
            if resp:
                return resp
        start = datetime.now()
        resp = self.api_client.systems_view_one(system_symbol)
        self.logging_client.systems_view_one(
            system_symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            self.db_client.update(resp)
        return resp

    def system_shipyard(
        self, wp: Waypoint, force_update=False
    ) -> Shipyard or SpaceTradersResponse:
        """View the types of ships available at a shipyard.

        Args:
            `wp` (Waypoint): The waypoint to view the ships at.

        Returns:
            Either a list of ship types (symbols for purchase) or a SpaceTradersResponse object on failure.
        """
        if not force_update:
            resp = self.db_client.system_shipyard(wp)
            if bool(resp):
                return resp

        start = datetime.now()
        resp = self.api_client.system_shipyard(wp)
        self.logging_client.system_shipyard(
            wp, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            self.db_client.update(resp)
        return resp

    def system_market(
        self, wp: Waypoint, force_update=False
    ) -> Market or SpaceTradersResponse:
        if not force_update:
            resp = self.db_client.system_market(wp)
            if bool(resp):
                return resp

        start = datetime.now()
        resp = self.api_client.system_market(wp)
        self.logging_client.system_market(wp, (datetime.now() - start).total_seconds())
        if bool(resp):
            self.db_client.update(resp)
            return resp
        return resp

    def system_jumpgate(
        self, wp: Waypoint, force_update=False
    ) -> JumpGate or SpaceTradersResponse:
        """View the jumpgates at a waypoint. Note, requires a vessel to be at the waypoint to provide details.

        Args:
            `wp` (Waypoint): The waypoint to view the jumpgates at.

        Returns:
            Either a list of JumpGate objects or a SpaceTradersResponse object on failure.
        """

        if not force_update:
            resp = self.db_client.system_jumpgate(wp)
            if bool(resp):
                return resp

        start = datetime.now()
        resp = self.api_client.system_jumpgate(wp)

        self.logging_client.system_jumpgate(
            wp, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            self.db_client.update(resp)
        return resp

    def view_available_ships_details(
        self, wp: Waypoint
    ) -> dict[str:ShipyardShip] or SpaceTradersResponse:
        """view the available ships at a shipyard. Note, requires a vessel to be at the waypoint to provide details

        Args:
            `wp` (Waypoint): The waypoint to view the ships at.

        Returns:
            Either a dict of ShipyardShip objects or a SpaceTradersResponse object on failure.
        """

        url = _url(f"systems/{wp.system_symbol}/waypoints/{wp.symbol}/shipyard")
        resp = get_and_validate(url, headers=self._headers())
        if resp and (resp.data is None or "ships" not in resp.data):
            return LocalSpaceTradersRespose(
                "No ship at this waypoint to get details.", 200, 0, url
            )
        if resp:
            return {d["type"]: ShipyardShip.from_json(d) for d in resp.data["ships"]}

        return resp

    def find_surveys(self, waypoint_symbol: str = None) -> list[Survey]:
        """filter cached surveys by system, and material

        Args:
            `waypoint_symbol` (str): Optional - The symbol of the waypoint to filter by.

        Returns:
            A list of Survey objects that match the filter. If no filter is provided, all surveys are returned.
        """
        pass

    def find_survey_best_deposit(
        self, waypoint_symbol: str, deposit_symbol: str
    ) -> Survey or SpaceTradersResponse:
        """find the survey with the best chance of giving a specific material.

        Args:
            `material_symbol` (str): Required - The symbol of the material we're looking for.
            `waypoint_symbol` (str): Optional - The symbol of the waypoint to filter by.

        Returns:
            A Survey object that has the best chance of giving the material. If no matching survey is found, None is returned.
        """

        survey = self.db_client.find_survey_best_deposit(
            waypoint_symbol, deposit_symbol
        )
        return survey

    def find_survey_best(self, waypoint_symbol: str) -> Survey or SpaceTradersResponse:
        """find the survey with the best chance of giving a specific material.

        Args:
            `waypoint_symbol` (str): Optional - The symbol of the waypoint to filter by.

        REturns:
            A Survey object that has the best chance of giving the material. If no matching survey is found, None is returned.
        """
        survey = self.db_client.find_survey_best(waypoint_symbol)
        return survey

    def find_waypoint_by_coords(self, system: str, x: int, y: int) -> Waypoint or None:
        """find a waypoint by its coordinates. Only searches cached values.

        Args:
            `system` (str): The symbol of the system to search in.
            `x` (int): The x coordinate of the waypoint.
            `y` (int): The y coordinate of the waypoint.

        Returns:
            Either a Waypoint object or None if no matching waypoint is found.
        """
        for waypoint in self.waypoints.values():
            if waypoint.system_symbol == system and waypoint.x == x and waypoint.y == y:
                return waypoint
        return None

    def find_waypoints_by_type(
        self, system_wp, waypoint_type
    ) -> list[Waypoint] or SpaceTradersResponse:
        """find a waypoint by its type. searches cached values first, then makes a request if no match is found.

        Args:
            `system_wp` (str): The symbol of the system to search in.
            `waypoint_type` (str): The type of waypoint to search for.

        returns:
            Either a Waypoint object or a SpaceTradersResponse object on API failure.
            If no matching waypoint is found and no errors occur, None is returned."""

        resp = []
        for wayp in self.waypoints_view(system_wp).values():
            wayp: Waypoint
            if wayp.type == waypoint_type:
                resp.append(wayp)

        if isinstance(resp, list) and len(resp) > 0:
            return resp
        resp = self.db_client.find_waypoints_by_type(system_wp, waypoint_type)
        if resp:
            return resp

        start = datetime.now()
        wayps = self.api_client.find_waypoints_by_type(system_wp, waypoint_type)
        self.logging_client.find_waypoints_by_trait(
            system_wp, waypoint_type, wayps, (datetime.now() - start).total_seconds()
        )
        if isinstance(wayps, list):
            wayps: list
            for wayp in wayps:
                self.db_client.update(wayp)
                self.update(wayp)
            return wayps
        return LocalSpaceTradersRespose(
            "Could not find any waypoints with that trait.",
            0,
            0,
            f"{__name__}.find_waypoints_by_trait",
        )

    def find_waypoints_by_type_one(
        self, system_wp, waypoint_type
    ) -> Waypoint or SpaceTradersResponse or None:
        """find a waypoint by its type. searches cached values first, then makes a request if no match is found.

        Args:
            `system_wp` (str): The symbol of the system to search in.
            `waypoint_type` (str): The type of waypoint to search for.

        returns:
            Either a Waypoint object or a SpaceTradersResponse object on API failure.
            If no matching waypoint is found and no errors occur, None is returned.
        """
        for waypoint in self.waypoints.values():
            if waypoint.system_symbol == system_wp and waypoint.type == waypoint_type:
                return waypoint
        resp = self.waypoints_view(system_wp)
        if not resp:
            return resp
        for waypoint in self.waypoints_view(system_wp).values():
            if waypoint.type == waypoint_type:
                return waypoint

    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        resp = []
        for wayp in self.waypoints_view(system_symbol).values():
            wayp: Waypoint
            for wp_trait in wayp.traits:
                if wp_trait.symbol == trait:
                    resp.append(wayp)

        if isinstance(resp, list) and len(resp) > 0:
            return resp
        resp = self.db_client.find_waypoints_by_trait(system_symbol, trait)
        if resp:
            return resp

        start = datetime.now()
        wayps = self.api_client.find_waypoints_by_trait(system_symbol, trait)
        self.logging_client.find_waypoints_by_trait(
            system_symbol, trait, wayps, (datetime.now() - start).total_seconds()
        )
        if isinstance(wayps, list):
            wayps: list
            for wayp in wayps:
                self.db_client.update(wayp)
                self.update(wayp)
            return wayps
        return LocalSpaceTradersRespose(
            "Could not find any waypoints with that trait.",
            0,
            0,
            f"{__name__}.find_waypoints_by_trait",
        )

    def find_waypoints_by_trait_one(
        self, system_wp: str, trait_symbol: str
    ) -> Waypoint or None:
        """find a waypoint by its trait. searches cached values first, then makes a request if no match is found.
        If there are multiple matching waypoints, only the first one is returned.

        Args:
            `system_wp` (str): The symbol of the system to search in.
            `trait_symbol` (str): The symbol of the trait to search for.

        Returns:
            Either a Waypoint object or None if no matching waypoint is found."""
        for waypoint in self.waypoints.values():
            for trait in waypoint.traits:
                if waypoint.system_symbol == system_wp and trait.symbol == trait_symbol:
                    return waypoint
        resp = self.waypoints_view(system_wp)
        if not resp:
            return resp
        for waypoint in resp.values():
            waypoint: Waypoint
            for trait in waypoint.traits:
                if trait.symbol == trait_symbol:
                    return waypoint

    def ship_orbit(self, ship: "Ship"):
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        if ship.nav.status == "IN_ORBIT":
            return LocalSpaceTradersRespose(
                None, 200, "Ship is already in orbit", "client_mediator.ship_orbit()"
            )
        start = datetime.now()
        resp = self.api_client.ship_orbit(ship)
        self.logging_client.ship_orbit(
            ship, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.db_client.update(ship)
        return

    def ship_patch_nav(self, ship: "Ship", flight_mode: str):
        """my/ships/:shipSymbol/course"""
        start = datetime.now()
        resp = self.api_client.ship_patch_nav(ship, flight_mode)
        self.logging_client.ship_patch_nav(
            ship, flight_mode, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update({"nav": resp.data})
            self.update(ship)

        return resp

    def ship_move(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/navigate"""
        if ship.nav.waypoint_symbol == dest_waypoint_symbol:
            return LocalSpaceTradersRespose(
                f"Navigate request failed. Ship '{ship.name}' is currently located at the destiatnion.",
                400,
                4204,
                "client_mediator.ship_move()",
            )

        start = datetime.now()
        resp = self.api_client.ship_move(ship, dest_waypoint_symbol)
        self.logging_client.ship_move(
            ship, dest_waypoint_symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.db_client.update(ship)
            self.ships[ship.name] = ship
        return resp

    def ship_jump(self, ship: "Ship", dest_system_symbol: str):
        """my/ships/:shipSymbol/jump"""
        start = datetime.now()
        resp = self.api_client.ship_jump(ship, dest_system_symbol)
        self.logging_client.ship_jump(
            ship, dest_system_symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.update(ship)
            self.ships[ship.name] = ship
        return resp

    def ship_negotiate(self, ship: "Ship") -> "Contract" or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/negotiate/contract"""
        if ship.nav.status != "DOCKED":
            self.ship_dock(ship)

        start = datetime.now()
        resp = self.api_client.ship_negotiate(ship)
        self.logging_client.ship_negotiate(
            ship, resp, (datetime.now() - start).total_seconds()
        )
        if bool(resp):
            self.update(resp)
        return resp

    def ship_extract(self, ship: "Ship", survey: Survey = None) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""
        # 4228 / 400 - MAXIMUM CARGO, should not extract
        #

        start = datetime.now()
        resp = self.api_client.ship_extract(ship, survey)
        self.logging_client.ship_extract(
            ship, survey, resp, (datetime.now() - start).total_seconds()
        )
        if resp.data is not None:
            ship.update(resp.data)
            self.update(ship)
        if not resp:
            if resp.error_code in [4224, 4221, 4220]:
                self.surveys_mark_exhausted(survey.signature)
            else:
                self.logger.error(
                    "status_code = %s, error_code = %s,  error = %s",
                    resp.status_code,
                    resp.error_code,
                    resp.error,
                )
        return resp

    def ship_refine(self, ship: Ship, trade_symbol: str):
        """/my/ships/{shipSymbol}/refine"""
        start = datetime.now()
        resp = self.api_client.ship_refine(ship, trade_symbol)
        self.logging_client.ship_refine(
            ship, trade_symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.db_client.update(ship)
            self.update(ship)
        return resp

    def ship_install_mount(
        self, ship: "Ship", mount_symbol: str, duration: float = None
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/install"""
        start = datetime.now()
        resp = self.api_client.ship_install_mount(ship, mount_symbol)
        self.logging_client.ship_install_mount(
            ship, mount_symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.update(ship)
        return resp

    def ship_remove_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/remove"""
        start = datetime.now()
        resp = self.api_client.ship_remove_mount(ship, mount_symbol)
        self.logging_client.ship_remove_mount(
            ship, mount_symbol, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.update(ship)
        return resp

    def surveys_mark_exhausted(self, survey_signature) -> None:
        """Removes a survey from any caching - called after an invalid survey response."""
        self.db_client.surveys_mark_exhausted(survey_signature)
        self.logging_client.surveys_mark_exhausted(survey_signature)
        pass

    def ship_dock(self, ship: "Ship"):
        """/my/ships/{shipSymbol}/dock"""

        start = datetime.now()
        resp = self.api_client.ship_dock(ship)
        self.logging_client.ship_dock(
            ship, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.db_client.update(ship)
        return resp

    def ship_refuel(self, ship: "Ship"):
        """/my/ships/{shipSymbol}/refuel"""

        start = datetime.now()
        resp = self.api_client.ship_refuel(ship)
        self.logging_client.ship_refuel(
            ship, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.db_client.update(ship)

    def ship_sell(
        self, ship: "Ship", symbol: str, quantity: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""

        start = datetime.now()
        resp = self.api_client.ship_sell(ship, symbol, quantity)
        self.logging_client.ship_sell(
            ship, symbol, quantity, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.update(ship)
            self.update(resp.data)
        return resp

    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity
    ) -> SpaceTradersResponse:
        start = datetime.now()
        resp = self.api_client.ship_purchase_cargo(ship, symbol, quantity)
        self.logging_client.ship_purchase_cargo(
            ship, symbol, quantity, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_survey(self, ship: "Ship") -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""

        start = datetime.now()
        resp = self.api_client.ship_survey(ship)
        self.logging_client.ship_survey(
            ship, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            surveys = [Survey.from_json(d) for d in resp.data.get("surveys", [])]
            for survey in surveys:
                self.db_client.update(survey)
            self.update(resp.data)
            ship.update(resp.data)
            self.update(ship)

        elif resp.data is not None:
            self.update(resp.data)
        return resp

    def ship_transfer_cargo(self, ship: "Ship", trade_symbol, units, target_ship_name):
        """/my/ships/{shipSymbol}/transfer"""

        start = datetime.now()
        resp = self.api_client.ship_transfer_cargo(
            ship, trade_symbol, units, target_ship_name
        )
        self.logging_client.ship_transfer_cargo(
            ship,
            trade_symbol,
            units,
            target_ship_name,
            resp,
            (datetime.now() - start).total_seconds(),
        )
        if resp:
            ship.update(resp.data)
            self.db_client.update(ship)
        return resp

    def ship_cooldown(self, ship: "Ship", force=False) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        if not force:
            resp = self.db_client.ship_cooldown(ship)
            if resp:
                ship.update(resp.data)
                # we just updated it from the DB, so don't recommit
                ship.cooldown_dirty = False
                self.update(ship)
                return resp

        start = datetime.now()
        resp = self.api_client.ship_cooldown(ship)
        self.logging_client.ship_cooldown(
            ship, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.update(ship)
        return resp

    def ship_jettison_cargo(
        self, ship: Ship, trade_symbol: str, quantity: int
    ) -> SpaceTradersResponse:
        start = datetime.now()
        resp = self.api_client.ship_jettison_cargo(ship, trade_symbol, quantity)
        self.logging_client.ship_jettison_cargo(
            ship, trade_symbol, quantity, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            ship.update(resp.data)
            self.update(ship)
        return resp

    def contracts_deliver(
        self, contract: Contract, ship: Ship, trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        start = datetime.now()
        resp = self.api_client.contracts_deliver(contract, ship, trade_symbol, units)
        self.logging_client.contracts_deliver(
            contract,
            ship,
            trade_symbol,
            units,
            resp,
            (datetime.now() - start).total_seconds(),
        )
        if resp:
            self.update(resp.data)
            contract.update(resp.data.get("contract", {}))
            ship.update(resp.data)
            self.db_client.update(ship)
        return resp

    def contracts_fulfill(self, contract: "Contract") -> SpaceTradersResponse:
        """/my/contracts/{contractId}/fulfill"""
        start = datetime.now()
        resp = self.api_client.contracts_fulfill(contract)
        self.logging_client.contracts_fulfill(
            contract, resp, (datetime.now() - start).total_seconds()
        )
        if resp:
            self.update(resp)
            self.db_client.update(contract)
            for deliverable in contract.deliverables:
                total_price = (
                    contract.payment_upfront - contract.payment_completion
                ) / len(contract.deliverables)
                transaction = {
                    "transaction": {
                        "waypointSymbol": deliverable.destination_symbol,
                        "shipSymbol": "GLOBAL",
                        "tradeSymbol": deliverable.symbol,
                        "type": contract.type,
                        "units": deliverable.units_fulfilled,
                        "pricePerUnit": total_price / deliverable.units_fulfilled,
                        "totalPrice": total_price,
                    }
                }
                self.logging_client.update(transaction)

            self.db_client.update(resp)
        return resp

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}
