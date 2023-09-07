from ..models import Agent
from ..local_response import LocalSpaceTradersRespose
import logging
import datetime


def _upsert_agent(connection, agent: Agent):
    sql = """INSERT INTO public.agents(
	agent_symbol, headquarters, credits, starting_faction, ship_count, last_updated)
	VALUES (%s, %s, %s, %s, %s, now() at time zone 'utc' ) on conflict(agent_symbol) do update set 
    credits = %s,
    last_updated = now() at time zone 'utc'"""

    cur = connection.cursor()
    cur.execute(
        sql,
        (
            agent.symbol,
            agent.headquarters,
            agent.credits,
            agent.starting_faction,
            agent.ship_count,
            agent.credits,
        ),
    )


def select_agent_one(connect, agent_symbol: str) -> Agent or "SpaceTradersResponse":
    sql = """select agent_symbol, headquarters, credits, starting_faction, ship_count, last_updated
    from agents where agent_symbol = %s"""
    try:
        cur = connect.cursor()
        cur.execute(sql, (agent_symbol,))
        resp = cur.fetchone()
    except Exception as err:
        logging.error(err)
        return LocalSpaceTradersRespose(err, 0, 0, f"{__name__}.select_agent_one")
    if not resp:
        return LocalSpaceTradersRespose(
            "Agent not found", 0, 0, f"{__name__}.select_agent_one"
        )
    return Agent(resp[0], resp[1], resp[2], resp[3], resp[4], None)
