from ..models import Agent
from ..local_response import LocalSpaceTradersRespose
import logging
import datetime
from ..utils import try_execute_upsert


def _upsert_extraction(
    connection, extraction: dict, session_id: str, waypoint_symbol, survey_signature
):
    sql = """INSERT INTO public.extractions(
	ship_symbol, session_id, event_timestamp, waypoint_symbol, survey_signature, trade_symbol, quantity)
	VALUES (%s,%s,  now() at time zone 'utc', %s, %s, %s, %s); """
    try_execute_upsert(
        connection,
        sql,
        (
            extraction["shipSymbol"],
            session_id,
            waypoint_symbol,
            survey_signature,
            extraction["yield"]["symbol"],
            extraction["yield"]["units"],
        ),
    )
