from ..models_misc import Agent
from ..resp_local_resp import LocalSpaceTradersRespose
import logging
import datetime

from ..utils import try_execute_upsert


def _upsert_transaction(transaction: dict, session_id: str, connection):
    sql = """INSERT INTO transactions(
	waypoint_symbol, ship_symbol, trade_symbol, type, units, price_per_unit, total_price, session_id, timestamp)
	VALUES (%s, %s, %s,%s,%s,%s, %s, %s, now() at time zone 'utc' ) on conflict(ship_symbol, timestamp) do nothing """

    params = (
        transaction["waypointSymbol"],
        transaction["shipSymbol"],
        transaction["tradeSymbol"],
        transaction["type"],
        transaction["units"],
        transaction["pricePerUnit"],
        transaction["totalPrice"],
        session_id,
    )
    return try_execute_upsert(sql, params, connection)
