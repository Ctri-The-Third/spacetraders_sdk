from ..models import Agent
from ..local_response import LocalSpaceTradersRespose
import logging
import datetime


def _upsert_transaction(connection, transaction: dict, session_id: str):
    sql = """INSERT INTO transactions(
	waypoint_symbol, ship_symbol, trade_symbol, type, units, price_per_unit, total_price, session_id, timestamp)
	VALUES (%s, %s, %s,%s,%s,%s, %s, %s, now() at time zone 'utc' ) on conflict(ship_symbol, timestamp) do nothing """

    cur = connection.cursor()
    cur.execute(
        sql,
        (
            transaction["waypointSymbol"],
            transaction["shipSymbol"],
            transaction["tradeSymbol"],
            transaction["type"],
            transaction["units"],
            transaction["pricePerUnit"],
            transaction["totalPrice"],
            session_id,
        ),
    )
