from ..models import Agent
from ..local_response import LocalSpaceTradersRespose
import logging
import datetime
from ..utils import try_execute_upsert, try_execute_select


def _upsert_agent(agent: Agent):
    sql = """INSERT INTO public.agents(
	agent_symbol, headquarters, credits, starting_faction, ship_count, last_updated)
	VALUES (%s, %s, %s, %s, %s, now() at time zone 'utc' ) on conflict(agent_symbol) do update set 
    credits = %s,
    last_updated = now() at time zone 'utc'"""

    return try_execute_upsert(
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


def select_agent_one(agent_symbol: str) -> Agent or "SpaceTradersResponse":
    sql = """select agent_symbol, headquarters, credits, starting_faction, ship_count, last_updated
    from agents where agent_symbol = %s"""
    resp = try_execute_select(sql, (agent_symbol,))

    if resp:
        return Agent(resp[0][0], resp[0][1], resp[0][2], resp[0][3], resp[0][4], None)
    return resp
