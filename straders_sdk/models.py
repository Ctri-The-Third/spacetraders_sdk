from dataclasses import dataclass
from datetime import datetime, timedelta
import requests

from .utils import DATE_FORMAT


class SymbolClass:
    symbol: str

    def __str__(self) -> str:
        return self.symbol


@dataclass
class Announement:
    id: int
    title: str
    body: str


@dataclass
class CrewInfo:
    pass


@dataclass
class FuelInfo:
    pass


@dataclass
class ShipRequirements:
    crew: int = 0
    module_slots: int = 0
    power: int = 0

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(*json_data.values())


@dataclass
class ShipFrame(SymbolClass):
    symbol: str
    name: str
    description: str
    module_slots: int
    mounting_points: int
    fuel_capacity: int
    condition: int
    requirements: ShipRequirements
    pass

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data["symbol"],
            json_data["name"],
            json_data["description"],
            json_data["moduleSlots"],
            json_data["mountingPoints"],
            json_data["fuelCapacity"],
            json_data.get("condition", 0),
            ShipRequirements.from_json(json_data["requirements"]),
        )


class ShipModule:
    symbol: str
    capacity: int
    name: str
    description: str
    requirements: ShipRequirements

    def __init__(self, json_data: dict) -> None:
        self.symbol = json_data["symbol"]
        self.capacity = json_data.get("capacity", None)
        self.range = json_data.get("range", None)
        self.name = json_data["name"]
        self.description = json_data["description"]
        self.requirements = ShipRequirements.from_json(
            json_data.get("requirements", {})
        )

    # this is our standard, even if we're using it to call the default constructor
    @classmethod
    def from_json(cls, json_data: dict):
        return cls(json_data)


@dataclass
class Deposit:
    symbol: str


class ShipMount:
    symbol: str
    name: str
    description: str
    strength: int
    deposits: list[Deposit]
    requirements: dict

    def __init__(self, json_data: dict) -> None:
        self.symbol = json_data["symbol"]
        self.name = json_data["name"]
        self.description = json_data.get("description", None)
        self.strength = json_data.get("strength", None)

        self.deposits = [Deposit(d) for d in json_data.get("deposits", [])]
        self.requirements = ShipRequirements.from_json(json_data["requirements"])

    # this is our standard, even if we're using it to call the default constructor
    @classmethod
    def from_json(cls, json_data: dict):
        return cls(json_data)


@dataclass
class ShipReactor(SymbolClass):
    symbol: str
    name: str
    description: str
    condition: int
    power_output: int
    requirements: ShipRequirements
    pass

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data["symbol"],
            json_data["name"],
            json_data["description"],
            json_data.get("condition", 0),
            json_data["powerOutput"],
            ShipRequirements.from_json(json_data["requirements"]),
        )


@dataclass
class ShipEngine(SymbolClass):
    symbol: str
    name: str
    description: str
    condition: int
    speed: int
    requirements: ShipRequirements

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data["symbol"],
            json_data["name"],
            json_data["description"],
            json_data.get("condition", 0),
            json_data["speed"],
            ShipRequirements.from_json(json_data["requirements"]),
        )


## this should/could be a waypoint.
@dataclass
class RouteNode:
    symbol: str
    type: str
    systemSymbol: str
    x: int
    y: int

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(*json_data.values())


@dataclass
class ShipNav:
    system_symbol: str
    waypoint_symbol: str
    destination: RouteNode
    origin: RouteNode
    arrival_time: datetime
    departure_time: datetime
    status: str
    flight_mode: str

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data["systemSymbol"],
            json_data["waypointSymbol"],
            RouteNode.from_json(json_data["route"]["destination"]),
            RouteNode.from_json(json_data["route"]["departure"]),
            datetime.strptime(json_data["route"]["arrival"], DATE_FORMAT),
            datetime.strptime(json_data["route"]["departureTime"], DATE_FORMAT),
            json_data["status"],
            json_data["flightMode"],
        )

    @property
    def travel_time_remaining(self) -> int:
        if self.status == "IN_TRANSIT":
            return (
                self.arrival_time - min(self.arrival_time, datetime.utcnow())
            ).seconds
        return 0


@dataclass
class Survey:
    signature: str
    symbol: str
    deposits: list[Deposit]
    expiration: datetime
    size: str
    _json: dict
    times_used: int = 0

    @classmethod
    def from_json(cls, json_data: dict):
        deposit_objs = [Deposit(**deposit) for deposit in json_data.get("deposits", [])]

        return cls(
            signature=json_data.get("signature"),
            symbol=json_data.get("symbol"),
            deposits=deposit_objs,
            expiration=datetime.strptime(json_data.get("expiration"), DATE_FORMAT),
            size=json_data.get("size"),
            _json=json_data,
        )

    def to_json(self):
        return self._json


@dataclass
class ShipRoute:
    origin: RouteNode
    destination: RouteNode
    departure_time: datetime
    arrival: datetime


@dataclass
class Agent:
    def __init__(
        self,
        symbol: str,
        headquarters: str,
        credits: int,
        starting_faction: str,
        ship_count: int = None,
        account_id: str = None,
    ):
        self.symbol = symbol
        self.headquarters = headquarters
        self.credits = credits
        self.starting_faction = starting_faction
        self.ship_count = ship_count
        self.account_id = account_id

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data["symbol"],
            json_data["headquarters"],
            json_data["credits"],
            json_data["startingFaction"],
            json_data.get("shipCount", None),
            json_data.get("accountId", None),
        )

    def update(self, json_data: dict):
        if "agent" in json_data:
            self.symbol = json_data["agent"]["symbol"]
            self.headquarters = json_data["agent"]["headquarters"]
            self.credits = json_data["agent"]["credits"]
            self.starting_faction = json_data["agent"]["startingFaction"]
            self.ship_count = json_data["agent"].get("shipCount", self.ship_count)
            self.account_id = json_data["agent"].get("accountId", self.account_id)


@dataclass
class WaypointTrait(SymbolClass):
    symbol: str
    name: str = ""
    description: str = ""


@dataclass
class Waypoint(SymbolClass):
    system_symbol: str
    symbol: str
    type: str
    x: int
    y: int
    oribtals: list
    traits: list[WaypointTrait]
    chart: dict
    faction: dict

    @classmethod
    def from_json(cls, json_data: dict):
        # a waypoint can be a fully scanned thing, or a stub from scanning the system.
        # future C'tri - there are actually two different kinds of waypoint, SystemWaypoint and Waypoint.
        if "orbitals" not in json_data:
            json_data["orbitals"] = []
        if "traits" not in json_data:
            json_data["traits"] = []
        if "chart" not in json_data:
            json_data["chart"] = {}
        if "faction" not in json_data:
            json_data["faction"] = {}
        return_obj = cls(
            json_data["systemSymbol"],
            json_data["symbol"],
            json_data["type"],
            json_data["x"],
            json_data["y"],
            json_data["orbitals"],
            json_data["traits"],
            json_data["chart"],
            json_data["faction"],
        )
        new_traits = []
        for old_trait in return_obj.traits:
            new_traits.append(WaypointTrait(*old_trait.values()))
        return_obj.traits = new_traits
        return return_obj

    @property
    def is_charted(self) -> bool:
        charted = self.chart is not None and len(self.chart) > 0
        return charted or (
            len(self.traits) > 1
            and ("UNCHARTED" not in [t.symbol for t in self.traits])
        )

    @property
    def has_shipyard(self) -> bool:
        return "SHIPYARD" in [t.symbol for t in self.traits]

    @property
    def has_market(self) -> bool:
        return "MARKETPLACE" in [t.symbol for t in self.traits]

    def has_jump_gate(self) -> bool:
        return "JUMP_GATE" in [t.symbol for t in self.traits]

    def __str__(self):
        return self.symbol

    def __hash__(self) -> int:
        return self.symbol.__hash__()

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Waypoint):
            return self.symbol == o.symbol
        return False

    def __lt__(self, o: object) -> bool:
        if isinstance(o, Waypoint):
            return self.symbol < o.symbol
        return False

    def __le__(self, o: object) -> bool:
        if isinstance(o, Waypoint):
            return self.symbol <= o.symbol
        return False

    def __gt__(self, o: object) -> bool:
        if isinstance(o, Waypoint):
            return self.symbol > o.symbol
        return False

    def __ge__(self, o: object) -> bool:
        if isinstance(o, Waypoint):
            return self.symbol >= o.symbol
        return False

    def __ne__(self, o: object) -> bool:
        if isinstance(o, Waypoint):
            return self.symbol != o.symbol
        return False


class JumpGate:
    def __init__(
        self,
        waypoint_symbol: str,
        connected_waypoints: list["str"],
    ) -> None:
        self.waypoint_symbol = waypoint_symbol
        self.connected_waypoints = connected_waypoints

    @classmethod
    def from_json(cls, waypoint_symbol, json_data: dict):
        return cls(
            waypoint_symbol,
            [wp for wp in json_data["connections"]],
        )


@dataclass
class System(SymbolClass):
    symbol: str
    sector_symbol: str
    system_type: str
    x: int
    y: int
    waypoints: list[Waypoint]

    @classmethod
    def from_json(cls, json_data: dict):
        wayps = []
        for wp in json_data.get("waypoints", []):
            wp["systemSymbol"] = json_data["symbol"]
            wayps.append(Waypoint.from_json(wp))
        return cls(
            json_data["symbol"],
            json_data["sectorSymbol"],
            json_data["type"],
            json_data["x"],
            json_data["y"],
            wayps,
        )

    def to_json(self) -> dict:
        "does not include waypoints"
        return {
            "symbol": self.symbol,
            "sectorSymbol": self.sector_symbol,
            "type": self.system_type,
            "x": self.x,
            "y": self.y,
            "waypoints": [],
        }

    def __hash__(self) -> int:
        return self.symbol.__hash__()

    def __eq__(self, o: object) -> bool:
        if isinstance(o, System):
            return self.symbol == o.symbol
        return False

    def __lt__(self, o: object) -> bool:
        if isinstance(o, System):
            return self.symbol < o.symbol
        return False

    def __le__(self, o: object) -> bool:
        if isinstance(o, System):
            return self.symbol <= o.symbol
        return False

    def __gt__(self, o: object) -> bool:
        if isinstance(o, System):
            return self.symbol > o.symbol
        return False

    def __ge__(self, o: object) -> bool:
        if isinstance(o, System):
            return self.symbol >= o.symbol
        return False

    def __ne__(self, o: object) -> bool:
        if isinstance(o, System):
            return self.symbol != o.symbol
        return False


@dataclass
class JumpGateConnection(SymbolClass):
    symbol: str
    sector_symbol: str
    type: str

    x: int
    y: int
    distance: int
    faction_symbol: str = ""

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data["symbol"],
            json_data["sectorSymbol"],
            json_data["type"],
            json_data["x"],
            json_data["y"],
            json_data["distance"],
            json_data.get("factionSymbol", ""),
        )


class ShipyardShip:
    def __init__(
        self,
        frame: ShipFrame,
        reactor: ShipReactor,
        engine: ShipEngine,
        name,
        description,
        ship_type,
        purchase_price,
        modules,
        mounts,
    ):
        self.frame = frame
        self.reactor = reactor
        self.engine = engine
        self.name = name
        self.description = description
        self.ship_type = ship_type
        self.purchase_price = purchase_price
        self.modules = modules
        self.mounts = mounts

    @classmethod
    def from_json(cls, json_data: dict):
        frame = ShipFrame.from_json(json_data["frame"])
        reactor = ShipReactor.from_json(json_data["reactor"])
        engine = ShipEngine.from_json(json_data["engine"])
        name = json_data["name"]
        description = json_data["description"]
        ship_type = json_data["type"]
        purchase_price = json_data["purchasePrice"]

        modules = [ShipModule(d) for d in json_data["modules"]]
        mounts = [ShipMount(d) for d in json_data["mounts"]]
        return cls(
            frame,
            reactor,
            engine,
            name,
            description,
            ship_type,
            purchase_price,
            modules,
            mounts,
        )


@dataclass
class Shipyard:
    waypoint: str
    ship_types: list[str]
    ships: dict[str, ShipyardShip] = None

    @classmethod
    def from_json(cls, json_data: dict):
        types = [type_["type"] for type_ in json_data["shipTypes"]]
        ships = {
            ship["type"]: ShipyardShip.from_json(ship)
            for ship in json_data.get("ships", [])
        }

        return cls(json_data["symbol"], types, ships)


class RateLimitDetails:
    def __init__(self, response: requests.Response) -> None:
        self.rate_limit_type: str = response.headers.get("x-ratelimit-type")
        self.limit: int = int(response.headers.get("x-ratelimit-limit"))
        self.limit_remaining: int = int(response.headers.get("x-ratelimit-remaining"))
        self.reset_time: datetime = datetime.strptime(
            response.headers.get("x-ratelimit-reset"), DATE_FORMAT
        )
        self.limit_burst: int = int(response.headers.get("x-ratelimit-burst"))
        self.limit_per_second: int = int(response.headers.get("x-ratelimit-per-second"))
        pass


class GameStatus:
    "response from {url}/{version}/"

    def __init__(self, json_data: dict):
        self._json_data = json_data
        self.status: str = self._json_data["status"]
        self.version: str = self._json_data["version"]
        self.reset_date = self._json_data["resetDate"]
        self.description: str = self._json_data["description"]
        self.total_agents: int = self._json_data["stats"]["agents"]
        self.total_systems: int = self._json_data["stats"]["systems"]
        self.total_ships: int = self._json_data["stats"]["ships"]
        self.total_waypoints: int = self._json_data["stats"]["waypoints"]
        self.next_reset = datetime.strptime(
            self._json_data["serverResets"]["next"], DATE_FORMAT
        )
        self.announcements = []
        for announcement in self._json_data["announcements"]:
            self.announcements.append(
                Announement(
                    len(self.announcements), announcement["title"], announcement["body"]
                )
            )


@dataclass
class MarketTradeGoodListing:
    symbol: str
    trade_volume: int
    type: str  # EXPORT, IMPORT, or EXCHANGE
    supply: str

    purchase_price: int
    sell_price: int
    recorded_ts: datetime = datetime.now()
    activity: str = None

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            json_data.get("symbol", None),
            json_data.get("tradeVolume", None),
            json_data.get("type", None),
            json_data.get("supply", None),
            json_data.get("purchasePrice", None),
            json_data.get("sellPrice", None),
            datetime.now(),
            json_data.get("activity", None),
        )


@dataclass
class MarketTradeGood:
    symbol: str
    name: str
    description: str


@dataclass
class Market:
    symbol: str
    exports: list[MarketTradeGood]
    imports: list[MarketTradeGood]
    exchange: list[MarketTradeGood]
    listings: list[MarketTradeGoodListing] = None

    @classmethod
    def from_json(cls, json_data: dict):
        exports = [MarketTradeGood(**export) for export in json_data["exports"]]
        imports = [MarketTradeGood(**import_) for import_ in json_data["imports"]]
        exchange = [MarketTradeGood(**listing) for listing in json_data["exchange"]]
        listings = []
        if "tradeGoods" in json_data:
            listings = [
                MarketTradeGoodListing.from_json(l) for l in json_data["tradeGoods"]
            ]
        return cls(json_data["symbol"], exports, imports, exchange, listings)

    def is_stale(self, age: int = 60):
        if not self.listings:
            return True

        target_time = datetime.now() - timedelta(minutes=age)
        for listing in self.listings:
            if listing.recorded_ts < target_time:
                return True
        return False

    def get_tradegood(self, symbol) -> MarketTradeGoodListing:
        for listing in self.listings:
            if listing.symbol == symbol:
                return listing
        for listing in self.exports:
            if listing.symbol == symbol:
                return listing
        for listing in self.imports:
            if listing.symbol == symbol:
                return listing
        for listing in self.exchange:
            if listing.symbol == symbol:
                return listing

        return None
