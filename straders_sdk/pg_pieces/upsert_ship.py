from ..ship import Ship
from ..models import Agent
import psycopg2
import logging
import re
import datetime
from ..local_response import LocalSpaceTradersRespose

# from psycopg2 import connection


def _upsert_ship(connection, ship: Ship, owner: Agent = None):
    try:
        match = re.findall(r"(.*)-[0-9A-F]+", ship.name)
        owner_name = match[0]
    except:
        return
    owner_faction = "" if not owner else owner.starting_faction
    sql = """INSERT into ships (ship_symbol, agent_name, faction_symbol, ship_role, cargo_capacity
    , cargo_in_use, fuel_capacity, fuel_current, last_updated)
        values (%s, %s, %s, %s, %s, %s, %s, %s, NOW() at time zone 'utc')
        ON CONFLICT (ship_symbol) DO UPDATE
        SET agent_name = %s,
            faction_symbol = %s,
            ship_role = %s,
            cargo_capacity = %s,
            cargo_in_use = %s, 
            fuel_capacity = %s,
            fuel_current = %s,
            last_updated = (NOW() at time zone 'utc') ;"""

    try_execute_upsert(
        connection,
        sql,
        (
            ship.name,
            owner_name,
            owner_faction,
            ship.role,
            ship.cargo_capacity,
            ship.cargo_units_used,
            ship.fuel_capacity,
            ship.fuel_current,
            owner_name,
            owner_faction,
            ship.role,
            ship.cargo_capacity,
            ship.cargo_units_used,
            ship.fuel_capacity,
            ship.fuel_current,
        ),
    )
    resp = _upsert_ship_nav(connection, ship)
    if not resp:
        return resp

    resp = _upsert_ship_frame(connection, ship)
    if not resp:
        return resp

    resp = _upsert_ship_cooldown(connection, ship)
    return resp


def _upsert_ship_nav(connection, ship: Ship):
    # we need to add offsets to the ship times to get them to UTC.
    sql = """INSERT into ship_nav
        (Ship_symbol, system_symbol, waypoint_symbol, departure_time, arrival_time, o_waypoint_symbol, d_waypoint_symbol, flight_status, flight_mode)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ship_symbol) DO UPDATE
        SET system_symbol = EXCLUDED.system_symbol,
            waypoint_symbol = EXCLUDED.waypoint_symbol,
            departure_time = EXCLUDED.departure_time,
            arrival_time = EXCLUDED.arrival_time,
            o_waypoint_symbol = EXCLUDED.o_waypoint_symbol,
            d_waypoint_symbol = EXCLUDED.d_waypoint_symbol,
            flight_status = EXCLUDED.flight_status,
            flight_mode = EXCLUDED.flight_mode;"""
    values = (
        ship.name,
        ship.nav.system_symbol,
        ship.nav.waypoint_symbol,
        ship.nav.departure_time,
        ship.nav.arrival_time,
        ship.nav.origin.symbol,
        ship.nav.destination.symbol,
        ship.nav.status,
        ship.nav.flight_mode,
    )
    resp = try_execute_upsert(connection, sql, values)
    return resp


def _upsert_ship_frame(connection, ship: Ship):
    """
    INSERT INTO public.ship_frames(
        frame_symbol, name, description, module_slots, mount_points, fuel_capacity, required_power, required_crew, required_slots)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    sql = """INSERT INTO ship_frames
    (frame_symbol, name, description, module_slots, mount_points, fuel_capacity, required_power, required_crew, required_slots)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (frame_symbol) DO NOTHING"""
    values = (
        ship.frame.symbol,
        ship.frame.name,
        ship.frame.description,
        ship.frame.module_slots,
        ship.frame.mounting_points,
        ship.frame.fuel_capacity,
        ship.frame.requirements.power,
        ship.frame.requirements.crew,
        ship.frame.requirements.module_slots,
    )
    resp = try_execute_upsert(connection, sql, values)
    if not resp:
        return resp

    """INSERT INTO public.ship_frame_links(
	ship_symbol, frame_symbol, condition)
	VALUES (?, ?, ?);"""
    sql = """INSERT INTO ship_frame_links 
    (ship_symbol, frame_symbol, condition)
    VALUES (%s, %s, %s) 
    ON CONFLICT (ship_symbol, frame_symbol) DO UPDATE set condition = %s;"""
    values = (ship.name, ship.frame.symbol, ship.frame.condition, ship.frame.condition)
    resp = try_execute_upsert(connection, sql, values)
    return resp


def _upsert_ship_cooldown(connection, ship: Ship):
    if ship.seconds_until_cooldown == 0:
        return LocalSpaceTradersRespose(
            None, None, None, url=f"{__name__}._upsert_ship_cooldown"
        )
    sql = """insert into ship_cooldowns  (ship_symbol, total_seconds, expiration)
    values (%s, %s, %s) ON CONFLICT (ship_symbol, expiration) DO NOTHING;"""
    values = (ship.name, ship._cooldown_length, ship._cooldown_expiration)
    resp = try_execute_upsert(connection, sql, values)
    return resp


def try_execute_upsert(connection, sql, params) -> LocalSpaceTradersRespose:
    try:
        cur = connection.cursor()
        cur.execute(sql, params)
        return LocalSpaceTradersRespose(
            None, None, None, url=f"{__name__}.try_execute_upsert"
        )
    except Exception as err:
        return LocalSpaceTradersRespose(
            error=err, status_code=0, error_code=0, url=f"{__name__}.try_execute_upsert"
        )
