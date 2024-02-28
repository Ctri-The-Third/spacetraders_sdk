from .pg_connection_pool import PGConnectionPool
from typing import Protocol
from .models_misc import (
    Waypoint,
    WaypointTrait,
    Market,
    Survey,
    Deposit,
    Shipyard,
    ShipyardShip,
    MarketTradeGood,
    MarketTradeGoodListing,
    System,
    Agent,
    JumpGate,
)
import logging
from .models_contracts import Contract, ContractDeliverGood
from datetime import datetime
from .responses import SpaceTradersResponse
from .client_interface import SpaceTradersClient
from .pg_pieces.upsert_waypoint import _upsert_waypoint
from .pg_pieces.upsert_shipyard import _upsert_shipyard
from .pg_pieces.upsert_market import _upsert_market
from .pg_pieces.upsert_ship import _upsert_ship
from .pg_pieces.upsert_system import _upsert_system
from .pg_pieces.upsert_survey import _upsert_survey
from .pg_pieces.select_ship import _select_ships, _select_ship_one
from .pg_pieces.jump_gates import _upsert_jump_gate, select_jump_gate_one
from .pg_pieces.agents import _upsert_agent, select_agent_one
from .pg_pieces.contracts import _upsert_contract
from .pg_pieces.construction_sites import (
    _upsert_construction_site,
    select_construction_site_one,
)
from .resp_local_resp import LocalSpaceTradersRespose
from .models_misc import RouteNode, ConstructionSite
from .models_ship import Ship, ShipInventory, ShipNav, ShipModule, ShipMount
from .utils import try_execute_select, try_execute_upsert
import psycopg2
from .constants import ORBITAL_TYPES, PARENT_TYPES


class SpaceTradersPostgresClient(SpaceTradersClient):
    token: str = None
    current_agent_symbol: str = None

    def __init__(
        self,
        db_host,
        db_name,
        db_user,
        db_pass,
        current_agent_symbol,
        db_port=None,
    ) -> None:
        if not db_host or not db_name or not db_user or not db_pass:
            raise ValueError("Missing database connection information")
        self._connection = None
        self.connection_pool = PGConnectionPool(
            db_user, db_pass, db_host, db_name, db_port
        )
        self.current_agent_symbol = current_agent_symbol
        self.logger = logging.getLogger(__name__)
        self._ship_mounts = {}
        self._ship_modules = {}

    @property
    def connection(self):
        if not self._connection:
            self._connection = self.connection_pool.get_connection()
        if self._connection.closed:
            self.connection_pool.return_connection(self._connection)
            self._connection = self.connection_pool.get_connection()
        return self._connection

    def release_connection(self):
        if self._connection:
            self.connection_pool.return_connection(self._connection)
            self._connection = None

    def assign_connection(self, connection):
        if isinstance(connection, psycopg2.extensions.connection):
            self._connection = connection
        else:
            raise ValueError("Connection must be a psycopg2 connection object")

    def _headers(self) -> dict:
        return {}

    def update(self, update_obj) -> SpaceTradersResponse:
        "Accepts objects and stores them in the DB"
        if isinstance(update_obj, JumpGate):
            return _upsert_jump_gate(update_obj, self.connection)
        if isinstance(update_obj, Survey):
            return _upsert_survey(update_obj, self.connection)
        if isinstance(update_obj, Waypoint):
            return _upsert_waypoint(update_obj, self.connection)
        if isinstance(update_obj, Shipyard):
            return _upsert_shipyard(update_obj, self.connection)
        if isinstance(update_obj, Market):
            return _upsert_market(update_obj, self.connection)
        if isinstance(update_obj, Ship):
            return _upsert_ship(update_obj, self.connection)
        if isinstance(update_obj, System):
            return _upsert_system(update_obj, self.connection)
        if isinstance(update_obj, Agent):
            return _upsert_agent(update_obj, self.connection)
        if isinstance(update_obj, Contract):
            return _upsert_contract(
                self.current_agent_symbol, update_obj, self.connection
            )
        if isinstance(update_obj, ConstructionSite):
            return _upsert_construction_site(update_obj, self.connection)

    def register(self, callsign, faction="COSMIC", email=None) -> SpaceTradersResponse:
        return dummy_response(__class__.__name__, "register")

    def agents_view_one(self, agent_symbol: str) -> Agent or SpaceTradersResponse:
        return select_agent_one(agent_symbol, self.connection)

    def set_current_agent(self, agent_symbol: str, token: str = None):
        self.current_agent_name = agent_symbol
        self.token = token

    def view_my_self(self) -> Agent or SpaceTradersResponse:
        return select_agent_one(self.current_agent_symbol, self.connection)

    def view_my_contracts(self) -> list["Contract"] or SpaceTradersResponse:
        sql = """select id --0
        , faction_symbol --1
        , type       --2
        , deadline   --3
        , expiration --4
        , fulfilled  --5
        , accepted   --6
        , co.payment_upfront  --7
        , co.payment_on_completion --8
        , ct.trade_symbol --9
        , ct.destination_symbol --10
        , ct.units_Required --11
        , ct.units_fulfilled --12
        from contracts co join contract_tradegoods ct on ct.contract_id = co.id
        where co.agent_symbol = %s
        """

        rows = try_execute_select(sql, (self.current_agent_symbol,), self.connection)
        if not rows:
            return rows
        contracts = []
        current_contract_id = ""
        new_contract = None
        rows.append(["ENDING", "", "", "", "", "", "", "", "", "", "", "", ""])
        for row in rows:
            if row[0] != "" and row[0] != current_contract_id:
                if new_contract is not None:
                    contracts.append(new_contract)

                new_contract = Contract(
                    row[0],  # id
                    row[1],  # faction
                    row[2],  # type
                    row[3],  # deadline
                    row[4],  # deadline_to_accept
                    row[4],
                    row[7],  # payment_upfront
                    row[8],  # payment_on_completion
                    [],  # deliverables
                    row[6],  # accepted
                    row[5],  # fulfilled
                )
            deliverable = ContractDeliverGood(row[9], row[10], row[11], row[12])
            new_contract.deliverables.append(deliverable)
        return contracts

    def waypoints_view(
        self, system_symbol: str
    ) -> dict[str:Waypoint] or SpaceTradersResponse:
        """view all waypoints in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoints in.

        Returns:
            Either a dict of Waypoint objects or a SpaceTradersResponse object on failure.
        """

        sql = """SELECT * FROM waypoints w 
        left join waypoint_charts wc on w.waypoint_symbol = wc.waypoint_symbol 
         
           WHERE system_symbol = %s"""
        rows = try_execute_select(sql, (system_symbol,), self.connection)
        waypoints = {}

        for row in rows:
            waypoint_symbol = row[0]
            new_sql = """SELECT * FROM waypoint_traits WHERE waypoint_symbol = %s"""
            trait_rows = try_execute_select(
                new_sql, (waypoint_symbol,), self.connection
            )
            traits = []
            for trait_row in trait_rows:
                traits.append(WaypointTrait(trait_row[1], trait_row[2], trait_row[3]))
            chart = {
                "waypointSymbol": row[6],
                "submittedBy": row[7],
                "submittedOn": row[8],
            }
            waypoint = Waypoint(
                row[2],
                row[0],
                row[1],
                row[3],
                row[4],
                [],
                traits,
                {},
                {},
                row[6],
                row[7],
            )
            waypoints[waypoint.symbol] = waypoint
        return waypoints

    def waypoints_view_one(
        self, waypoint_symbol, force=False
    ) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in. Has no impact in this client.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.
            `force` (bool): Optional - Force a refresh of the waypoint. Defaults to False.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""
        sql = """SELECT * FROM waypoints WHERE waypoint_symbol = %s LIMIT 1;"""
        rows = try_execute_select(sql, (waypoint_symbol,), self.connection)
        waypoints = []

        for row in rows:
            waypoint_symbol = row[0]
            new_sql = """SELECT * FROM waypoint_traits WHERE waypoint_symbol = %s"""

            trait_rows = try_execute_select(
                new_sql, (waypoint_symbol,), self.connection
            )
            traits = []
            for trait_row in trait_rows:
                traits.append(WaypointTrait(trait_row[1], trait_row[2], trait_row[3]))
            waypoint = Waypoint(
                row[2],
                row[0],
                row[1],
                row[3],
                row[4],
                [],
                traits,
                {},
                {},
                row[6],
                row[7],
            )
            waypoints.append(waypoint)

        if len(waypoints) > 0:
            waypoints[0]: Waypoint
            return waypoints[0]
        else:
            return LocalSpaceTradersRespose(
                "Could not find waypoint with that symbol in DB", 0, 0, sql
            )

    def find_waypoints_by_coords(
        self, system_symbol: str, x: int, y: int
    ) -> list[Waypoint] or SpaceTradersResponse:
        sql = """select w.waypoint_symbol, type, system_symbol, x, y, modifiers, under_construction, wt.trait_symbol, wt.name, wt.description 
        from waypoints w join waypoint_traits wt 
        on w.waypoint_symbol = wt.waypoint_symbol
        where system_symbol = %s and x = %s and y = %s"""
        rows = try_execute_select(sql, (system_symbol, x, y), self.connection)
        waypoints = {}
        waypoints: dict[str:Waypoint]
        for row in rows:
            (
                symbol,
                type,
                system_symbol,
                x,
                y,
                modifiers,
                under_construction,
                trait_symbol,
                name,
                description,
            ) = row
            if symbol not in waypoints:
                waypoints[symbol] = Waypoint(
                    system_symbol,
                    symbol,
                    type,
                    x,
                    y,
                    [],
                    [],
                    {},
                    {},
                    modifiers,
                    under_construction,
                )
            waypoints[symbol].traits.append(
                WaypointTrait(trait_symbol, name, description)
            )
        return waypoints

    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "find_waypoints_by_trait")

    def find_waypoints_by_trait_one(
        self, system_symbol: str, trait: str
    ) -> Waypoint or SpaceTradersResponse:
        pass

    def find_waypoints_by_type(
        self, system_wp: str, waypoint_type: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        db_wayps = self.waypoints_view(system_wp)
        if not db_wayps:
            return db_wayps
        return [wayp for wayp in db_wayps.values() if wayp.type == waypoint_type]

    def find_waypoints_by_type_one(
        self, system_wp: str, waypoint_type
    ) -> Waypoint or SpaceTradersResponse:
        db_wayps = self.waypoints_view(system_wp)
        if not db_wayps:
            return db_wayps
        try:
            return [wayp for wayp in db_wayps.values() if wayp.type == waypoint_type][0]
        except IndexError:
            pass
        return LocalSpaceTradersRespose(
            f"Couldn't find waypoint of type {waypoint_type} in system {system_wp}",
            0,
            0,
            f"find_waypoint_by_type({system_wp}, {waypoint_type})",
        )

    def find_survey_best_deposit(
        self, waypoint_symbol: str, deposit_symbol: str
    ) -> Survey or SpaceTradersResponse:
        sql = """select s.signature, s.waypoint_symbol, s.expiration, s.size 
                from survey_chance_and_values scv 
                join surveys s on scv.signature = s.signature 
                where trade_symbol = %s and waypoint_symbol = %s
                limit 1 
                """

        deposits_sql = (
            """select trade_symbol, count from survey_deposits where signature = %s """
        )
        resp = try_execute_select(
            sql, (deposit_symbol, (waypoint_symbol)), self.connection
        )
        if not resp:
            if isinstance(resp, list):
                return LocalSpaceTradersRespose(
                    "Didn't find a matching survey", 0, 0, sql
                )
            return resp
        surveys = []
        for survey_row in resp:
            deposits_resp = try_execute_select(
                deposits_sql, (survey_row[0],), self.connection
            )
            if not deposits_resp:
                return deposits_resp
            deposits = []
            deposits_json = []
            for deposit_row in deposits_resp:
                deposit = Deposit(deposit_row[0])
                for i in range(deposit_row[1]):
                    deposits.append(deposit)
                    deposits_json.append({"symbol": deposit.symbol})
            json = {
                "signature": survey_row[0],
                "symbol": survey_row[1],
                "deposits": deposits_json,
                "expiration": survey_row[2].isoformat(),
                "size": survey_row[3],
            }
            surveys.append(
                Survey(
                    survey_row[0],
                    survey_row[1],
                    deposits,
                    survey_row[2],
                    survey_row[3],
                    json,
                )
            )
        return surveys[0]

    def find_survey_best(self, waypoint_symbol: str):
        sql = """SELECT s.signature, s.waypoint_symbol, s.expiration, s.size 
                FROM survey_chance_and_values scv 
                JOIN surveys s on scv.signature = s.signature 
                WHERE waypoint_symbol = %s
                LIMIT 1 
                """

        deposits_sql = (
            """select trade_symbol, count from survey_deposits where signature = %s """
        )
        resp = try_execute_select(sql, (waypoint_symbol,), self.connection)
        if not resp:
            if isinstance(resp, list):
                return LocalSpaceTradersRespose(
                    "Didn't find a matching survey", 0, 0, sql
                )
            return resp
        surveys = []
        for survey_row in resp:
            deposits_resp = try_execute_select(
                deposits_sql, (survey_row[0],), self.connection
            )
            if not deposits_resp:
                return deposits_resp
            deposits = []
            deposits_json = []
            for deposit_row in deposits_resp:
                deposit = Deposit(deposit_row[0])
                for i in range(deposit_row[1]):
                    deposits.append(deposit)
                    deposits_json.append({"symbol": deposit.symbol})
            json = {
                "signature": survey_row[0],
                "symbol": survey_row[1],
                "deposits": deposits_json,
                "expiration": survey_row[2].isoformat(),
                "size": survey_row[3],
            }
            surveys.append(
                Survey(
                    survey_row[0],
                    survey_row[1],
                    deposits,
                    survey_row[2],
                    survey_row[3],
                    json,
                )
            )
        return surveys[0]

    def surveys_mark_exhausted(self, survey_signature) -> None:
        """Removes a survey from any caching - called after an invalid survey response."""
        sql = """update surveys s 
        set exhausted = True
        where signature = %s
        """
        resp = try_execute_upsert(sql, (survey_signature,), self.connection)
        return resp

    def ship_orbit(self, ship: "Ship") -> SpaceTradersResponse:
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        return dummy_response(__class__.__name__, "ship_orbit")
        pass

    def ship_patch_nav(self, ship: "Ship", flight_mode: str):
        """my/ships/:shipSymbol/course"""
        return dummy_response(__class__.__name__, "ship_patch_nav")
        pass

    def ship_move(
        self, ship: "Ship", dest_waypoint_symbol: str
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/navigate"""

        return dummy_response(__class__.__name__, "ship_move")
        pass

    def ship_create_chart(self, ship: "Ship"):
        """my/ships/:shipSymbol/chart"""
        return dummy_response(__class__.__name__, "ship_create_chart")
        pass

    def ship_scan_ships(self, ship: "Ship") -> list["Ship"] or SpaceTradersResponse:
        """my/ships/:shipSymbol/scan"""

        return dummy_response(__class__.__name__, "ship_scan_ships")

    def ship_warp(
        self, ship: "Ship", dest_waypoint_symbol: str
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/warp"""

        return dummy_response(__class__.__name__, "ship_warp")
        pass

    def ship_jump(
        self, ship: "Ship", dest_waypoint_symbol: str
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/jump"""
        return dummy_response(__class__.__name__, "ship_jump")
        pass

    def ship_negotiate(self, ship: "Ship") -> "Contract" or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "ship_negotiate")

    def ship_siphon(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/siphon"""
        return dummy_response(__class__.__name__, "ship_siphon")
        pass

    def ship_extract(self, ship: "Ship", survey: Survey = None) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""

        return dummy_response(__class__.__name__, "ship_extract")
        pass

    def ship_refine(self, ship: "Ship", trade_symbol: str) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refine"""

        return dummy_response(__class__.__name__, "ship_refine")
        pass

    def ship_dock(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/dock"""
        return dummy_response(__class__.__name__, "ship_dock")
        pass

    def ship_refuel(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refuel"""
        return dummy_response(__class__.__name__, "ship_refuel")
        pass

    def ship_sell(
        self, ship: "Ship", symbol: str, quantity: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""
        # on a sell we need to remove X of a value from the database.
        #
        pass

    def ship_purchase_cargo(
        self, ship: "Ship", symbol: str, quantity
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/purchase"""
        return dummy_response(__class__.__name__, "ship_purchase_cargo")
        pass

    def ship_survey(self, ship: "Ship") -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""
        return dummy_response(__class__.__name__, "ship_survey")
        pass

    def ship_transfer_cargo(
        self, ship: "Ship", trade_symbol, units, target_ship_name
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/transfer"""
        return dummy_response(__class__.__name__, "ship_transfer_cargo")
        pass

    def ship_install_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/install"""
        return dummy_response(__class__.__name__, "ship_install_mount")
        pass

    def ship_remove_mount(
        self, ship: "Ship", mount_symbol: str
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/mounts/remove"""
        return dummy_response(__class__.__name__, "ship_remove_mount")
        pass

    def ship_jettison_cargo(
        self, ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/jettison"""

        pass

    def system_construction(self, wp: Waypoint) -> SpaceTradersResponse:
        """/game/systems/{symbol}/construction"""
        return select_construction_site_one(wp.symbol, self.connection)
        pass

    def construction_supply(self, wp, ship, trade_symbol, quantity):
        pass

    def system_market(self, wp: Waypoint) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""
        try:
            sql = """SELECT mt.trade_symbol, mt.name, mt.description, mt.type, FROM market_tradegoods mt where mt.market_symbol =  %s"""
            rows = try_execute_select(sql, (wp.symbol,), self.connection)
            if not rows:
                return LocalSpaceTradersRespose(
                    f"Could not find market data for that waypoint", 0, 0, sql
                )
            imports = [MarketTradeGood(*row[0:3]) for row in rows if row[3] == "IMPORT"]
            exports = [MarketTradeGood(*row[0:3]) for row in rows if row[3] == "EXPORT"]
            exchanges = [
                MarketTradeGood(*row[0:3]) for row in rows if row[3] == "EXCHANGE"
            ]

            listings_sql = """select trade_symbol, market_depth , type,  supply, purchase_price, sell_price, last_updated, activity
                            from market_tradegood_listings mtl
                            where market_symbol = %s"""
            rows = try_execute_select(listings_sql, (wp.symbol,), self.connection)
            listings = [MarketTradeGoodListing(*row) for row in rows]
            return Market(wp.symbol, imports, exports, exchanges, listings)
        except Exception as err:
            return LocalSpaceTradersRespose(
                f"Could not find market data for that waypoint - {err}", 0, 0, sql
            )

    def system_jumpgate(self, wp: Waypoint) -> JumpGate or SpaceTradersResponse:
        return select_jump_gate_one(wp, self.connection)

    def systems_view_twenty(
        self, page_number: int, force=False
    ) -> list["System"] or SpaceTradersResponse:
        return dummy_response(__class__.__name__, "systems_view_twenty")

    def systems_view_all(self) -> list["Waypoint"] or SpaceTradersResponse:
        """/game/systems"""
        sql = """SELECT system_symbol, sector_symbol, type, x, y FROM systems"""
        rows = try_execute_select(sql, (), self.connection)
        cysts = {}
        for row in rows:
            syst = System(row[0], row[1], row[2], row[3], row[4], [])
            cysts[syst.symbol] = syst
        return cysts

    def systems_view_one(self, system_symbol: str) -> Waypoint or SpaceTradersResponse:
        sql = """SELECT system_symbol, sector_symbol, type, x, y FROM systems where system_symbol = %s limit 1"""

        rows = try_execute_select(sql, (system_symbol,), self.connection)
        if not rows:
            return rows
        for row in rows:
            syst = System(row[0], row[1], row[2], row[3], row[4], [])

            waypoints = self.waypoints_view(system_symbol)
            syst.waypoints = [w for w in waypoints.values()]
            return syst

    def system_shipyard(self, wp: Waypoint) -> Shipyard or SpaceTradersResponse:
        """View the types of ships available at a shipyard.

        Args:
            `wp` (Waypoint): The waypoint to view the ships at.

        Returns:
            Either a list of ship types (symbols for purchase) or a SpaceTradersResponse object on failure.
        """
        sql = """SELECT ship_type, ship_cost  FROM shipyard_types where shipyard_symbol = %s"""
        rows = try_execute_select(sql, (wp.symbol,), self.connection)
        if not rows:
            return rows
        if len(rows) >= 1:
            types = [row[0] for row in rows]
            ships = {
                row[0]: ShipyardShip(
                    None, None, None, row[0], None, row[0], row[1], [], []
                )
                for row in rows
            }
            found_shipyard = Shipyard(wp.symbol, types, ships)
            return found_shipyard

    def ship_cooldown(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        sql = """select total_seconds, expiration from ship_cooldown where ship_symbol = %s"""
        resp = try_execute_select(sql, (ship.name,), self.connection)
        if not resp:
            return resp
        expiration = resp[0][1]
        expiration: datetime

        data = {
            "cooldown": {
                "shipSymbol": ship.name,
                "totalSeconds": resp[0][0],
                "remainingSeconds": 0,
                "expiration": f"{expiration.isoformat()}Z",
            }
        }
        resp = LocalSpaceTradersRespose(
            None, 0, None, url=f"{__class__.__name__}.ship_cooldown"
        )
        resp.data = data
        return resp

    def ships_purchase(
        self, ship_type: str, shipyard_waypoint: str
    ) -> tuple["Ship", "Agent"] or SpaceTradersResponse:
        dummy_response(__class__.__name__, "ships_purchase")

    def ships_view(self) -> dict[str:"Ship"] or SpaceTradersResponse:
        """/my/ships"""

        # PROBLEM - the client doesn't really know who the current agent is - so we can't filter by agent.
        # but the DB is home to many ships. Therefore, this client needs to become aware of the agent name on init.
        # WAIT WE ALREADY DO THAT. well done past C'tri

        resp = _select_ships(self.current_agent_symbol, self)

        if resp:
            return_obj = {}
            for ship in resp.values():
                return_obj[ship.name] = self._extend_ship_mount_modules(ship)
            return return_obj
        return

    def ships_view_one(self, symbol: str) -> "Ship" or SpaceTradersResponse:
        """/my/ships/{shipSymbol}"""
        resp = _select_ship_one(symbol, self)
        if resp:
            ship = self._extend_ship_mount_modules(resp[symbol])
            return ship
        return

    def contracts_deliver(
        self, contract: "Contract", ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        dummy_response(__class__.__name__, "contracts_deliver")
        pass

    def contracts_fulfill(self, contract: "Contract") -> SpaceTradersResponse:
        dummy_response(__class__.__name__, "contracts_fulfill")
        pass

    def _extend_ship_mount_modules(self, ship: "Ship"):
        """Extend the modules of a ship with the modules in the list."""
        if len(self._ship_mounts) == 0:
            sql = """select mount_symbol, mount_name, mount_Desc, strength, required_crew, required_power from ship_mounts"""

            rows = try_execute_select(sql, (), self.connection)
            for row in rows:
                mount = ShipMount(
                    {
                        "symbol": row[0],
                        "name": row[1],
                        "description": row[2],
                        "strength": row[3],
                        "requirements": {
                            "crew": row[4],
                            "module_slots": -1,
                            "power": row[5],
                        },
                    }
                )
                self._ship_mounts[row[0]] = mount

        # for module in ship.modules:
        #    if module.symbol in self._ship_modules.keys():
        #        module = self._ship_modules[module.symbol]
        for index in range(len(ship.mounts)):
            mount = ship.mounts[index]
            if isinstance(mount, str) and mount in self._ship_mounts.keys():
                ship.mounts[index] = self._ship_mounts[mount]
        return ship


def dummy_response(class_name, method_name):
    return LocalSpaceTradersRespose(
        "Not implemented in this client", 0, 0, f"{class_name}.{method_name}"
    )
