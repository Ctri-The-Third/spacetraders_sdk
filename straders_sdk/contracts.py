from datetime import datetime

from .client_interface import SpaceTradersClient
from .utils import DATE_FORMAT, _url, post_and_validate
from .models import SymbolClass
from dataclasses import dataclass
import logging

LOGGER = logging.getLogger("contracts")


@dataclass
class ContractDeliverGood(SymbolClass):
    symbol: str
    destination_symbol: str
    units_required: int
    units_fulfilled: int


# this should probably be its own thing


class Contract:
    id: str
    faction_symbol: str
    type: str
    deadline: datetime
    payment_upfront: int
    payment_completion: int
    deliverables: list[ContractDeliverGood]
    accepted: bool
    fulfilled: bool
    expiration: datetime
    deadline_to_accept: datetime = None
    token: str = None
    client: SpaceTradersClient = None

    def __init__(
        self,
        id,
        faction_symbol,
        type,
        deadline,
        expiration,
        deadline_to_accept,
        payment_upfront,
        payment_completion,
        deliverables,
        accepted,
        fulfilled,
    ) -> None:
        self.id = id
        self.faction_symbol = faction_symbol
        self.type = type
        self.deadline = deadline
        self.expiration = expiration
        self.deadline_to_accept = deadline_to_accept
        self.payment_upfront = payment_upfront
        self.payment_completion = payment_completion
        self.deliverables = deliverables
        self.accepted = accepted
        self.fulfilled = fulfilled

    @classmethod
    def from_json(cls, json_data: dict):
        id = json_data["id"]
        faction_symbol = json_data["factionSymbol"]
        type = json_data["type"]
        deadline = datetime.strptime(json_data["terms"]["deadline"], DATE_FORMAT)
        expiration = datetime.strptime(json_data["expiration"], DATE_FORMAT)

        deadline_to_accept = (
            datetime.strptime(json_data["deadlineToAccept"], DATE_FORMAT)
            if json_data["deadlineToAccept"] is not None
            else None
        )
        payment_upfront = json_data["terms"]["payment"]["onAccepted"]
        payment_completion = json_data["terms"]["payment"]["onFulfilled"]
        deliverables = [
            ContractDeliverGood(*d.values())
            for d in json_data["terms"].get("deliver", [])
        ]
        accepted = json_data["accepted"]
        fulfilled = json_data["fulfilled"]
        return cls(
            id,
            faction_symbol,
            type,
            deadline,
            expiration,
            deadline_to_accept,
            payment_upfront,
            payment_completion,
            deliverables,
            accepted,
            fulfilled,
        )

    def update(self, json_data: dict):
        self.from_json(json_data)
