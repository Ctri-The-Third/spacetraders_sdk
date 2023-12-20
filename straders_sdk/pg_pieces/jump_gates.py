from ..models import Waypoint, JumpGate, JumpGateConnection
import logging
from datetime import datetime
from ..local_response import LocalSpaceTradersRespose
from ..utils import try_execute_select, try_execute_upsert, waypoint_slicer


def _upsert_jump_gate(connect, jump_gate: JumpGate):
    sql = """INSERT INTO public.jump_gates(
	waypoint_symbol)
	VALUES (%s) on conflict do nothing;"""
    resp = try_execute_upsert(
        connect,
        sql,
        (jump_gate.waypoint_symbol,),
    )
    if not resp:
        return resp

    connection_sql = """INSERT INTO public.jumpgate_connections(
	s_waypoint_symbol, s_system_symbol, d_waypoint_symbol, d_system_symbol)
	VALUES (%s, %s, %s, %s) on conflict do nothing;"""

    for dest_waypoint in jump_gate.connected_waypoints:
        dest_waypoint: str
        resp = try_execute_upsert(
            connect,
            connection_sql,
            (
                jump_gate.waypoint_symbol,
                waypoint_slicer(jump_gate.waypoint_symbol),
                dest_waypoint,
                waypoint_slicer(dest_waypoint),
            ),
        )
        if not resp:
            return resp

        if not resp:
            return resp

    return LocalSpaceTradersRespose(None, 0, 0, url=f"{__name__}._upsert_jump_gate")


def select_jump_gate_one(connection, waypoint: Waypoint):
    sql = (
        """SELECT waypoint_symbol  FROM public.jump_gates WHERE waypoint_symbol = %s"""
    )
    resp = try_execute_select(connection, sql, (waypoint.symbol,))
    if not resp:
        return resp

    connection_sql = """
    select  jc.d_system_symbol 
    from jumpgate_connections jc
    where s_waypoint_symbol = %s"""
    conn_resp = try_execute_select(connection, connection_sql, (waypoint.symbol,))
    if not conn_resp:
        return conn_resp
    for one_row in resp:
        resp_obj = JumpGate(one_row[0], [l[0] for l in conn_resp])

    return resp_obj
