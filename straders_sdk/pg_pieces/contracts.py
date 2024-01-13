from ..models import Waypoint
from ..contracts import Contract, ContractDeliverGood
import logging
from datetime import datetime
from ..local_response import LocalSpaceTradersRespose
from ..utils import try_execute_select, try_execute_upsert


def _upsert_contract(agent_symbol: str, contract: Contract, connection):
    sql = """INSERT INTO public.contracts(
            id, agent_symbol, faction_symbol, type, payment_upfront, payment_on_completion, accepted, fulfilled, expiration, deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET 
            accepted = EXCLUDED.accepted,
            fulfilled = EXCLUDED.fulfilled;"""

    resp = try_execute_upsert(
        sql,
        (
            contract.id,
            agent_symbol,
            contract.faction_symbol,
            contract.type,
            contract.payment_upfront,
            contract.payment_completion,
            contract.accepted,
            contract.fulfilled,
            contract.expiration,
            contract.deadline,
        ),
        connection,
    )
    if not resp:
        return resp

    tradegood_sql = """INSERT INTO public.contract_tradegoods(
        contract_id, trade_symbol, destination_symbol, units_required, units_fulfilled)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (contract_id, trade_symbol) DO UPDATE SET
        destination_symbol = EXCLUDED.destination_symbol,
        units_required = EXCLUDED.units_required,
        units_fulfilled = EXCLUDED.units_fulfilled;"""

    for d in contract.deliverables:
        d: ContractDeliverGood
        resp = try_execute_upsert(
            tradegood_sql,
            (
                contract.id,
                d.symbol,
                d.destination_symbol,
                d.units_required,
                d.units_fulfilled,
            ),
            connection,
        )
        if not resp:
            return resp
    return LocalSpaceTradersRespose(None, 0, 0, url=f"{__name__}._upsert_jump_gate")
