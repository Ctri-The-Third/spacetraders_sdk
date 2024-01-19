from .models import Waypoint
from .responses import SpaceTradersResponse
from .client_interface import SpaceTradersClient
from .responses import SpaceTradersResponse
from .utils import (
    ApiConfig,
    _url,
    get_and_validate,
    patch_and_validate,
    post_and_validate,
    get_and_validate_paginated,
    get_and_validate_page,
    waypoint_slicer,
)
from .local_response import LocalSpaceTradersRespose  #
from .models import (
    Waypoint,
    Survey,
    Market,
    MarketTradeGoodListing,
    ConstructionSite,
    ConstructionSiteMaterial,
    Shipyard,
    System,
    JumpGate,
    Agent,
    Faction,
)
from .contracts import Contract
from .ship import Ship
import logging
from requests_ratelimiter import LimiterSession
from datetime import datetime

logger = logging.getLogger(__name__)
COOLDOWN_OFFSET = -2
MOVEMENT_OFFSET = -2


class SpaceTradersApiClient(SpaceTradersClient):
    "implements SpaceTradersClient Protocol. No in-memory caching, no database, just the API."

    def __init__(
        self,
        token=None,
        base_url=None,
        version=None,
        session: LimiterSession = None,
        connection=None,
        priority=5,
    ) -> None:
        self.token = token
        self.config = ApiConfig(base_url, version)
        self.current_agent = None
        self.current_agent_symbol = None
        self.session = session
        self.priority = priority
        pass

    def agents_view_one(self, agent_symbol: str) -> "Agent" or SpaceTradersResponse:
        url = _url(f"/agents/{agent_symbol}")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            return Agent.from_json(resp.data)
        return resp

    def set_current_agent(self, agent_symbol: str, token: str = None):
        self.current_agent_symbol = agent_symbol
        self.token = token
        self.current_agent = None

    def view_my_self(self) -> "Agent" or SpaceTradersResponse:
        url = _url("my/agent")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            self.current_agent = Agent.from_json(resp.data)
            self.current_agent_symbol = self.current_agent.symbol
            return self.current_agent
        return resp
        pass

    def view_my_contracts(self) -> list["Contract"] or SpaceTradersResponse:
        url = _url("my/contracts")
        resp = get_and_validate_paginated(
            url, 20, 50, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            return [Contract.from_json(d) for d in resp.data]
        return resp

    def waypoints_view_one(
        self, waypoint_symbol, force=False
    ) -> Waypoint or SpaceTradersResponse:
        system_symbol = waypoint_slicer(waypoint_symbol)
        if waypoint_symbol == "":
            raise ValueError("waypoint_symbol cannot be empty")
        url = _url(f"systems/{system_symbol}/waypoints/{waypoint_symbol}")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if not resp:
            print(resp.error)
            return resp
        wayp = Waypoint.from_json(resp.data)

        return wayp

    def waypoints_view(
        self, system_symbol: str
    ) -> dict[str:list] or SpaceTradersResponse:
        """view all waypoints in a system.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoints in.

        Returns:
            Either a dict of Waypoint objects or a SpaceTradersResponse object on failure.
        """
        pass

        url = _url(f"systems/{system_symbol}/waypoints")
        resp = get_and_validate_paginated(
            url,
            20,
            50,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            new_wayps = {d["symbol"]: Waypoint.from_json(d) for d in resp.data}
            return new_wayps
        return resp

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def update(self, response_json: dict):
        pass

    def list_factions(self) -> list[Faction] or SpaceTradersResponse:
        url = _url("/factions")
        resp = get_and_validate_paginated(url, 20, 2)
        if resp:
            return [Faction.from_json(d) for d in resp.data]
        return resp

    def register(self, callsign, faction="COSMIC", email=None) -> SpaceTradersResponse:
        url = _url("register")
        data = {"symbol": callsign, "faction": faction}
        if email is not None:
            data["email"] = email
        resp = post_and_validate(
            url, data, session=self.session, priority=self.priority
        )
        if resp:
            self.token = resp.data.get("token")
        return resp

    def ship_orbit(self, ship: Ship):
        "my/ships/:miningShipSymbol/orbit thakes the ship name or the ship object"
        url = _url(f"my/ships/{ship.name}/orbit")
        if ship.nav.status == "IN_ORBIT":
            return LocalSpaceTradersRespose(None, 0, None, url=url)
        resp = post_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            self.update(resp.data)
        return resp

    def ship_patch_nav(self, ship: Ship, flight_mode: str):
        "my/ships/:shipSymbol/nav"
        url = _url(f"my/ships/{ship.name}/nav")
        data = {"flightMode": flight_mode}
        resp = patch_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            self.update(resp.data)
        return resp

    def ship_move(self, ship: Ship, dest_waypoint_symbol: str):
        "my/ships/:shipSymbol/navigate"

        #  4204{'message': 'Navigate request failed. Ship CTRI-4 is currently located at the destination.', 'code': 4204, 'data': {'shipSymbol': 'CTRI-4', 'destinationSymbol': 'X1-MP2-50435D'}}
        if ship.nav.status == "DOCKED":
            self.ship_orbit(ship)
        url = _url(f"my/ships/{ship.name}/navigate")
        data = {"waypointSymbol": dest_waypoint_symbol}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority + MOVEMENT_OFFSET,
        )
        if resp:
            self.update(resp.data)
        return resp

    def ship_scan_waypoints(self, ship: Ship) -> SpaceTradersResponse:
        """returns a list of waypoints that are in range. Triggers a cooldown.
        /my/ships/{shipSymbol}/scan/waypoints"""
        url = _url(f"my/ships/{ship.name}/scan/waypoints")
        resp = post_and_validate(
            url,
            headers=self._headers(),
            session=self.session,
            priority=self.priority - COOLDOWN_OFFSET,
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
            waypoints = []
            for waypoint in resp.data.get("waypoints"):
                waypoints.append(Waypoint.from_json(waypoint))
            return waypoints
        return resp

    def ship_scan_ships(self, ship: Ship) -> SpaceTradersResponse:
        """returns a list of ships that are in range. Triggers a cooldown.
        /my/ships/{shipSymbol}/scan/ships"""

        url = _url(f"my/ships/{ship.name}/scan/ships")
        resp = post_and_validate(
            url,
            headers=self._headers(),
            session=self.session,
            priority=self.priority - COOLDOWN_OFFSET,
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
            ships = []
            for ship in resp.data.get("ships"):
                ships.append(Ship.from_json(ship))
            return ships
        return resp

    def ship_warp(self, ship: Ship, dest_waypoint_symbol: str):
        "my/ships/:shipSymbol/warp"
        url = _url(f"my/ships/{ship.name}/warp")
        data = {"waypointSymbol": dest_waypoint_symbol}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority - COOLDOWN_OFFSET,
        )
        if resp:
            self.update(resp.data)
        return resp

    def ship_jump(self, ship: Ship, dest_waypoint_symbol: str):
        "my/ships/:shipSymbol/jump"
        url = _url(f"my/ships/{ship.name}/jump")
        data = {"waypointSymbol": dest_waypoint_symbol}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority - COOLDOWN_OFFSET,
        )
        if resp:
            self.update(resp.data)
        return resp

    def ship_negotiate(self, ship: "Ship") -> "Contract" or SpaceTradersResponse:
        "/my/ships/{shipSymbol}/negotiate/contract"
        url = _url(f"my/ships/{ship.name}/negotiate/contract")
        resp = post_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            resp = Contract.from_json(resp.data.get("contract"))
        return resp

    def ship_siphon(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/siphon"""

        url = _url(f"my/ships/{ship.name}/siphon")

        if not ship.can_siphon:
            return LocalSpaceTradersRespose("Ship cannot siphon", 0, 0, url=url)
        if ship.seconds_until_cooldown > 0:
            return LocalSpaceTradersRespose("Ship still on cooldown", 0, 4200, url=url)

        resp = post_and_validate(url=url, headers=self._headers(), session=self.session)
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_extract(self, ship: Ship, survey: Survey = None) -> SpaceTradersResponse:
        "/my/ships/{shipSymbol}/extract"

        url = (
            _url(f"my/ships/{ship.name}/extract/survey")
            if survey
            else _url(f"my/ships/{ship.name}/extract")
        )
        if not ship.can_extract:
            return LocalSpaceTradersRespose("Ship cannot extract", 0, 4227, url=url)

        if ship.seconds_until_cooldown > 0:
            return LocalSpaceTradersRespose("Ship still on cooldown", 0, 4200, url=url)

        data = survey.to_json() if survey is not None else None

        resp = post_and_validate(
            url,
            json=data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority + COOLDOWN_OFFSET,
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_refine(self, ship: Ship, trade_symbol: str) -> SpaceTradersResponse:
        "/my/ships/{shipSymbol}/refine"

        url = _url(f"my/ships/{ship.name}/refine")
        if not ship.can_refine:
            return LocalSpaceTradersRespose(
                "Ship cannot refine - doesn't have a refinery", 0, 4239, url=url
            )

        if ship.seconds_until_cooldown > 0:
            return LocalSpaceTradersRespose("Ship still on cooldown", 0, 4200, url=url)

        data = {"produce": trade_symbol}
        resp = post_and_validate(
            url, json=data, headers=self._headers(), session=self.session
        )

        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_dock(self, ship: Ship):
        "/my/ships/{shipSymbol}/dock"
        url = _url(f"my/ships/{ship.name}/dock")

        if ship.nav.status == "DOCKED":
            return LocalSpaceTradersRespose(None, 200, None, url=url)
        resp = post_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_refuel(self, ship: Ship, from_cargo: bool = False):
        "/my/ships/{shipSymbol}/refuel"
        body = {"fromCargo": from_cargo}
        if ship.nav.status == "IN_ORBIT":
            self.ship_dock(ship)
        if ship.nav.status != "DOCKED":
            ship.logger.error("Ship must be docked to refuel")

        url = _url(f"my/ships/{ship.name}/refuel")
        resp = post_and_validate(
            url,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
            json=body,
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_sell(self, ship: Ship, symbol: str, quantity: int) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""
        url = _url(f"my/ships/{ship.name}/sell")

        if ship.nav.status != "DOCKED":
            return LocalSpaceTradersRespose(
                "Ship must be docked to sell", 0, 0, url=url
            )

        data = {"symbol": symbol, "units": quantity}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/purchase"""

        url = _url(f"my/ships/{ship.name}/purchase")
        data = {"symbol": symbol, "units": quantity}
        resp = post_and_validate(
            url, data, headers=self._headers(), session=self.session
        )
        if resp:
            self.update(resp.data)
            ship.update(resp.data)
        return resp

    def ship_survey(self, ship: Ship) -> list[Survey] or SpaceTradersResponse:
        "/my/ships/{shipSymbol}/survey"
        # 400, 4223, 'Ship survey failed. Ship must be in orbit to perform this type of survey.'
        if ship.nav.status == "DOCKED":
            self.ship_orbit(ship)
        if not ship.can_survey:
            return LocalSpaceTradersRespose("Ship cannot survey", 0, 4240)
        if ship.seconds_until_cooldown > 0:
            return LocalSpaceTradersRespose("Ship still on cooldown", 0, 4000)
        url = _url(f"my/ships/{ship.name}/survey")
        resp = post_and_validate(
            url,
            headers=self._headers(),
            session=self.session,
            priority=self.priority + COOLDOWN_OFFSET,
        )

        self.update(resp.data)

        return resp

    def ship_transfer_cargo(
        self, ship: Ship, trade_symbol, units, target_ship_name: str
    ):
        "/my/ships/{shipSymbol}/transfer"

        # 4217{'message': 'Failed to update ship cargo. Cannot add 6 unit(s) to ship cargo. Exceeds max limit of 60.', 'code': 4217, 'data': {'shipSymbol': 'CTRI-1', 'cargoCapacity': 60, 'cargoUnits': 60, 'unitsToAdd': 6}}
        url = _url(f"my/ships/{ship.name}/transfer")
        data = {
            "tradeSymbol": trade_symbol,
            "units": units,
            "shipSymbol": target_ship_name,
        }
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        self.update(resp.data)

        return resp

    def ship_install_mount(self, ship: Ship, mount_symbol: str) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/install"""

        url = _url(f"my/ships/{ship.name}/mounts/install")
        data = {"symbol": mount_symbol}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            self.update(resp.data)

            ship.update(resp.data)
            self.update(ship)
        return resp

    def ship_remove_mount(self, ship: Ship, mount_symbol: str) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/remove"""

        url = _url(f"my/ships/{ship.name}/mounts/remove")
        data = {"symbol": mount_symbol}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            self.update(resp.data)

            ship.update(resp.data)
            self.update(ship)
        return resp

    def ship_jettison_cargo(
        self, ship: Ship, trade_symbol: str, quantity: int
    ) -> SpaceTradersResponse:
        url = _url(f"my/ships/{ship.name}/jettison")
        data = {"symbol": trade_symbol, "units": quantity}
        resp = post_and_validate(
            url, data, headers=self._headers(), priority=self.priority
        )
        if resp:
            ship.update(resp.data)
        return resp

    # find_waypoint_by_coords, find_waypoint_by_type, find_waypoints_by_trait, find_waypoints_by_trait_one, system_market_view

    def find_waypoints_by_trait(self, system_symbol: str, trait: str) -> list[Waypoint]:
        return dummy_response(__class__.__name__, "find_waypoints_by_trait")

    def find_waypoints_by_type(
        self, system_wp: str, waypoint_type: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "find_waypoints_by_type")

    def find_waypoints_by_type_one(self, system_wp, waypoint_type) -> Waypoint:
        return dummy_response(__class__.__name__, "find_waypoint_by_type")

    def find_waypoints_by_coords(self, system_symbol: str, x: int, y: int) -> Waypoint:
        return dummy_response(__class__.__name__, "find_waypoint_by_coords")

    def find_waypoints_by_trait_one(self, system_symbol: str, trait: str) -> Waypoint:
        return dummy_response(__class__.__name__, "find_waypoints_by_trait_one")

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

    def systems_view_twenty(
        self, page_number: int, force=False
    ) -> list["System"] or SpaceTradersResponse:
        url = _url("systems")
        resp = get_and_validate_page(
            url,
            page_number,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )

        if resp:
            resp = [System.from_json(system) for system in resp.data]
        return resp

    def systems_view_all(self) -> list[System] or SpaceTradersResponse:
        url = _url("systems")
        resp = get_and_validate_paginated(
            url,
            per_page=20,
            page_limit=999,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            resp = [System.from_json(d) for d in resp.data]
        return resp

    def systems_view_one(self, system_symbol: str) -> System or SpaceTradersResponse:
        url = _url(f"systems/{system_symbol}")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            return System.from_json(resp.data)
        return resp

    def system_construction(
        self, wp: Waypoint
    ) -> ConstructionSite or SpaceTradersResponse:
        url = _url(f"systems/{wp.system_symbol}/waypoints/{wp.symbol}/construction")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            return ConstructionSite.from_json(resp.data)
        return resp

    def system_market(self, wp: Waypoint) -> Market:
        # /systems/{systemSymbol}/waypoints/{waypointSymbol}/market
        url = _url(f"systems/{wp.system_symbol}/waypoints/{wp.symbol}/market")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            resp = Market.from_json(resp.data)
        return resp

    def system_shipyard(self, wp: Waypoint) -> Shipyard or SpaceTradersResponse:
        """View the types of ships available at a shipyard.

        Args:
            `wp` (Waypoint): The waypoint to view the ships at.

        Returns:
            Either a list of ship types (symbols for purchase) or a SpaceTradersResponse object on failure.
        """

        url = _url(f"systems/{wp.system_symbol}/waypoints/{wp.symbol}/shipyard")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )

        if resp:
            return Shipyard.from_json(resp.data)

        return resp

    def system_jumpgate(self, wp: Waypoint) -> JumpGate or SpaceTradersResponse:
        """/systems/{systemSymbol}/waypoints/{waypointSymbol}/jump-gate"""
        url = _url(f"systems/{wp.system_symbol}/waypoints/{wp.symbol}/jump-gate")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            gate = JumpGate.from_json(wp.symbol, resp.data)
            gate.waypoint_symbol = wp.symbol
            return gate
        return resp

    def ship_cooldown(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        # /my/ships/{shipSymbol}/cooldown
        url = _url(f"my/ships/{ship.name}/cooldown")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp and "expiration" in resp.data:
            ship.update({"cooldown": resp.data})
        else:
            ship._cooldown_expiration = datetime.utcnow()
        pass
        return resp

    def ships_view(self) -> dict[str:"Ship"] or SpaceTradersResponse:
        """/my/ships"""
        url = _url("my/ships")
        resp = get_and_validate_paginated(
            url,
            20,
            10,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if resp:
            resp = {ship["symbol"]: Ship.from_json(ship) for ship in resp.data}

        return resp

    def ships_view_one(self, symbol: str) -> "Ship" or SpaceTradersResponse:
        "/my/ships/{shipSymbol}"
        url = _url(f"my/ships/{symbol}")
        resp = get_and_validate(
            url, headers=self._headers(), session=self.session, priority=self.priority
        )
        if resp:
            return Ship.from_json(resp.data)
        return resp

    def ships_purchase(
        self, ship_type: str, shipyard_waypoint: str
    ) -> tuple[Ship, Agent] or SpaceTradersResponse:
        url = _url("my/ships")
        data = {"shipType": ship_type, "waypointSymbol": shipyard_waypoint}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        if not resp:
            return resp
        new_ship = Ship.from_json(resp.data.get("ship"))
        new_self = Agent.from_json(resp.data.get("agent"))
        return (new_ship, new_self)

    def construction_supply(
        self, waypoint: Waypoint, ship: Ship, trade_symbol: str, units: int
    ):
        url = _url(
            f"systems/{waypoint.system_symbol}/waypoints/{waypoint.symbol}/construction/supply"
        )
        data = {"shipSymbol": ship.name, "tradeSymbol": trade_symbol, "units": units}
        resp = post_and_validate(
            url,
            data,
            headers=self._headers(),
            session=self.session,
            priority=self.priority,
        )
        return resp

    def contracts_deliver(
        self, contract: Contract, ship: Ship, trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        url = _url(f"/my/contracts/{contract.id}/deliver")
        data = {"shipSymbol": ship.name, "tradeSymbol": trade_symbol, "units": units}
        headers = self._headers()
        resp = post_and_validate(
            url, data, headers=headers, session=self.session, priority=self.priority
        )
        if not resp:
            print(f"failed to deliver to contract {resp.status_code}, {resp.error}")
            return resp
        return resp

    def contracts_fulfill(self, contract: Contract):
        url = _url(f"/my/contracts/{contract.id}/fulfill")
        headers = self._headers()
        resp = post_and_validate(
            url, headers=headers, session=self.session, priority=self.priority
        )
        if not resp:
            print(f"failed to fulfill contract {resp.status_code}, {resp.error}")
            return resp
        if "contract" in resp.data:
            contract.update(resp.data["contract"])
        return contract


def dummy_response(class_name, method_name):
    return LocalSpaceTradersRespose(
        "Not implemented in this client", 0, 0, f"{class_name}.{method_name}"
    )
