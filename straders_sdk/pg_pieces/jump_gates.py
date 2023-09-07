from ..models import Waypoint, JumpGate, JumpGateConnection
import logging
from datetime import datetime
from ..local_response import LocalSpaceTradersRespose
from ..utils import try_execute_select, try_execute_upsert, waypoint_slicer


def _upsert_jump_gate(connect, jump_gate: JumpGate):
    sql = """INSERT INTO public.jump_gates(
	waypoint_symbol, faction_symbol, jump_range)
	VALUES (%s, %s, %s) on conflict do nothing;"""
    resp = try_execute_upsert(
        connect,
        sql,
        (jump_gate.waypoint_symbol, jump_gate.faction_symbol, jump_gate.jump_range),
    )
    if not resp:
        return resp

    connection_sql = """INSERT INTO public.jumpgate_connections(
	s_waypoint_symbol, s_system_symbol, d_system_symbol, distance)
	VALUES (%s, %s, %s, %s) on conflict do nothing;"""

    for connection in jump_gate.connected_waypoints:
        resp = try_execute_upsert(
            connect,
            connection_sql,
            (
                jump_gate.waypoint_symbol,
                waypoint_slicer(jump_gate.waypoint_symbol),
                connection.symbol,
                connection.distance,
            ),
        )
        if not resp:
            return resp

        resp = try_execute_upsert(
            connect,
            connection_sql,
            (
                None,
                connection.symbol,
                waypoint_slicer(jump_gate.waypoint_symbol),
                connection.distance,
            ),
        )
        if not resp:
            return resp

    return LocalSpaceTradersRespose(None, 0, 0, url=f"{__name__}._upsert_jump_gate")


def select_jump_gate_one(connection, waypoint: Waypoint):
    sql = """SELECT waypoint_symbol,  jump_range,  faction_symbol FROM public.jump_gates WHERE waypoint_symbol = %s"""
    resp = try_execute_select(connection, sql, (waypoint.symbol,))
    if not resp:
        return resp

    connection_sql = """
    select jc.d_system_symbol , s.sector_symbol, s.type, s.x, s.y, jc.distance

from jumpgate_connections jc 
left join systems s on jc.d_system_symbol = s.system_symbol
where s_waypoint_symbol = %s"""
    conn_resp = try_execute_select(connection, connection_sql, (waypoint.symbol,))
    if not conn_resp:
        return conn_resp
    for one_row in resp:
        resp_obj = JumpGate(one_row[0], one_row[1], [], one_row[2])
        for link_row in conn_resp:
            lr = JumpGateConnection(
                link_row[0],
                link_row[1],
                link_row[2],
                link_row[3],
                link_row[4],
                link_row[5],
                "",
            )
            resp_obj.connected_waypoints.append(lr)
    return resp_obj
