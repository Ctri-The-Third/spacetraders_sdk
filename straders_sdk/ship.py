from datetime import datetime, timedelta
from dataclasses import dataclass
from .models import CrewInfo, ShipFrame, FuelInfo, ShipModule, ShipMount
from .models import RouteNode, ShipReactor, ShipEngine, RouteNode, ShipRoute
from .models import ShipRequirements, ShipNav, Survey, Deposit
from .client_interface import SpaceTradersInteractive, SpaceTradersClient
from .client_stub import SpaceTradersStubClient
from .responses import SpaceTradersResponse
from .local_response import LocalSpaceTradersRespose
import logging
from .utils import parse_timestamp, get_and_validate, post_and_validate, _url
from .utils import SURVEYOR_SYMBOLS

from .responses import SpaceTradersResponse


### the question arises - if the Ship class is to have methods that interact with the server, which pattern do we use to implement that.
# choice - pass in a REFERENCE to the SpaceTraders class (which is kinda like a "session") -
#     example: https://github.com/cosmictraders/autotraders/blob/master/autotraders/space_traders_entity.py
#   - advantages = simple. if there's a st object we can just call, then everything becomes simple.
#   - disadvantage = we're creating a circle. the ST gets ships, ships call ST. It feels wrong.
#   - disadvantage = I feel the term dependency injection applies here? I need to research if that's inherently bad.
#
# choice - make Ship and ST alike inherit from a "client" class that has the token, and underlying generic methods that interact with the server.
#   - advantage = no circular dependency, code already exists.
#   - disadvantage = more complex, greater refactor, higher risk of me getting bored.
#
# what I read:
# * https://medium.com/@suneandreasdybrodebel/pythonic-dependency-injection-a-practical-guide-83a1b1299280
#   - I am absolutely not writing abstractions for everything, too much effort, low payoff, high chance of burnout
# * https://softwareengineering.stackexchange.com/questions/393065/can-we-completely-replace-inheritance-using-strategy-pattern-and-dependency-inje
# * https://www.thoughtworks.com/insights/blog/composition-vs-inheritance-how-choose
#   - this reminded me of the python `Protocol` thing I read about recently.
# protocols  https://andrewbrookins.com/technology/building-implicit-interfaces-in-python-with-protocol-classes/
#   - protocols appear to be the python equivelant of interfaces, which I'm avoiding.
# DECISION: second option, a "client" class that has the token, and underlying generic methods that interact with the server

# COMPLICATION: Circular imports, because SpaceTraders loads Ships, which loads responses, which loads ships.

# COUPLE-DAYS-LATER SOLUTION: I also ended up making an abstract response class after all, enables sending error "responses" locally without calling the API


@dataclass
class ShipInventory:
    symbol: str
    name: str
    description: str
    units: int

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(*json_data.values())


class Ship(SpaceTradersInteractive):
    name: str
    role: str
    faction: str
    nav: ShipNav
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    crew_capacity: int
    crew_current: int
    crew_required: int
    crew_rotation: str
    crew_morale: int
    crew_wages: int
    cargo_capacity: int
    cargo_units_used: int
    cargo_inventory: list[ShipInventory]
    # ---- FUEL INFO ----

    fuel_capacity: int
    fuel_current: int
    fuel_consumed_history: dict
    # needs expanded out into a class probably

    _cooldown_expiration = None
    _cooldown_length = 0
    # ----  REACTOR INFO ----

    # todo: modules and mounts
    modules: list[ShipModule]
    mounts: list[ShipMount]

    def __init__(self) -> None:
        pass

        self.logger = logging.getLogger("ship-logger")

    @property
    def can_survey(self) -> bool:
        for surveyor in SURVEYOR_SYMBOLS:
            if surveyor in [d.symbol for d in self.mounts]:
                return True
        return False

    @property
    def can_extract(self) -> bool:
        extractors = [
            "MOUNT_MINING_LASER_I",
            "MOUNT_MINING_LASER_II",
            "MOUNT_MINING_LASER_III",
        ]
        for extractor in extractors:
            if extractor in [d.symbol for d in self.mounts]:
                return True
        return False

    @property
    def can_refine(self) -> bool:
        refineries = ["MODULE_ORE_REFINERY_I"]
        for refinery in refineries:
            if refinery in [d.symbol for d in self.modules]:
                return True

    @property
    def cargo_space_remaining(self) -> int:
        return self.cargo_capacity - self.cargo_units_used

    @classmethod
    def from_json(
        cls,
        json_data: dict,
    ):
        ship = cls()
        ship.name: str = json_data.get("registration", {}).get("name", "")
        ship.role: str = json_data["registration"]["role"]
        ship.faction: str = json_data["registration"]["factionSymbol"]

        ship.nav = ShipNav.from_json(json_data["nav"])

        ship.frame = ShipFrame.from_json(json_data["frame"])
        ship.reactor = ShipReactor.from_json(json_data["reactor"])
        ship.engine = ShipEngine.from_json(json_data["engine"])

        # ------------------
        # ---- CREW INFO ----
        ship.crew_capacity: int = json_data["crew"]["capacity"]
        ship.crew_current: int = json_data["crew"]["current"]
        ship.crew_required: int = json_data["crew"]["required"]
        ship.crew_rotation: str = json_data["crew"]["rotation"]
        ship.crew_morale: int = json_data["crew"]["morale"]
        ship.crew_wages: int = json_data["crew"]["wages"]

        ship.cargo_capacity: int = json_data["cargo"]["capacity"]
        ship.cargo_units_used: int = json_data["cargo"]["units"]
        ship.cargo_inventory: list[ShipInventory] = [
            ShipInventory.from_json(d) for d in json_data["cargo"]["inventory"]
        ]

        # ---- FUEL INFO ----

        ship.fuel_capacity = json_data["fuel"]["capacity"]
        ship.fuel_current = json_data["fuel"]["current"]
        ship.fuel_consumed_history = json_data["fuel"]["consumed"]
        # needs expanded out into a class probably

        ship._cooldown_expiration: datetime = None
        ship._cooldown_length: int = 0
        # ----  REACTOR INFO ----

        # todo: modules and mounts
        ship.modules: list[ShipModule] = [ShipModule(d) for d in json_data["modules"]]
        ship.mounts: list[ShipMount] = [ShipMount(d) for d in json_data["mounts"]]
        return ship

    def orbit(self):
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        raise NotImplementedError

    def change_course(self, ship, dest_waypoint_symbol: str):
        raise NotImplementedError

    def move(self, dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/navigate"""

        raise NotImplementedError

    def extract(self, survey: Survey = None) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""
        raise NotImplementedError

    def dock(self):
        """/my/ships/{shipSymbol}/dock"""
        raise NotImplementedError

    def refuel(self):
        """/my/ships/{shipSymbol}/refuel"""
        raise NotImplementedError

    def sell(self, symbol: str, quantity: int):
        """/my/ships/{shipSymbol}/sell"""
        raise NotImplementedError

    def survey(self) -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""
        raise NotImplementedError

    def transfer_cargo(self, trade_symbol, units, target_ship_name):
        """/my/ships/{shipSymbol}/transfer"""
        raise NotImplementedError

    def receive_cargo(self, trade_symbol, units):
        for inventory_item in self.cargo_inventory:
            if inventory_item.symbol == trade_symbol:
                inventory_item.units += units
                return
        self.cargo_inventory.append(
            ShipInventory(
                trade_symbol,
                "this string came from receive cargo, shouldn't wind up in DB",
                "this string came from receive cargo, shouldn't wind up in DB",
                units,
            )
        )

    def force_update(self):
        # /my/ships/{shipSymbol}
        url = _url(f"my/ships/{self.name}")
        resp = get_and_validate(url, headers=self._headers())
        self.update(resp.data)
        return resp

    def update(self, json_data: dict):
        "Update the ship with the contents of a response object"
        if json_data is None:
            return

        if isinstance(json_data, dict):
            if "nav" in json_data:
                self.nav = ShipNav.from_json(json_data["nav"])
            if "cargo" in json_data:
                self.cargo_capacity = json_data["cargo"]["capacity"]
                self.cargo_units_used = json_data["cargo"]["units"]
                self.cargo_inventory: list[ShipInventory] = [
                    ShipInventory.from_json(d) for d in json_data["cargo"]["inventory"]
                ]
            if "cooldown" in json_data:
                self._cooldown_expiration = parse_timestamp(
                    json_data["cooldown"]["expiration"]
                )
                self._cooldown_length = json_data["cooldown"]["totalSeconds"]
                if self.seconds_until_cooldown > 6000:
                    self.logger.warning("Cooldown is over 100 minutes")
            if "fuel" in json_data:
                self.fuel_capacity = json_data["fuel"]["capacity"]
                self.fuel_current = json_data["fuel"]["current"]
                self.fuel_consumed_history = json_data["fuel"]["consumed"]
        # pass the updated ship to the client to be logged appropriately

    @property
    def seconds_until_cooldown(self) -> timedelta:
        if not self._cooldown_expiration:
            return 0
        time_to_wait = self._cooldown_expiration - datetime.utcnow()
        seconds = max(time_to_wait.seconds + (time_to_wait.days * 86400), 0)
        if seconds > 6000:
            self.logger.warning("Cooldown is over 100 minutes")
        return seconds
