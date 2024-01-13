from ..ship import Ship
from ..models import Agent
import psycopg2
import logging
import re
import datetime
from ..local_response import LocalSpaceTradersRespose
from ..utils import try_execute_upsert

# from psycopg2 import connection


def _upsert_ship(ship: Ship, connection, owner: Agent = None):
    try:
        match = re.findall(r"(.*)-[0-9A-F]+", ship.name)
        owner_name = match[0]
    except:
        return
    resp = LocalSpaceTradersRespose(None, 0, 0, url=f"{__name__}._upsert_ship")
    owner_faction = "" if not owner else owner.starting_faction
    sql = """INSERT into ships (ship_symbol, agent_name, faction_symbol, ship_role, cargo_capacity
    , cargo_in_use, fuel_capacity, fuel_current, mount_symbols, module_symbols, last_updated)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() at time zone 'utc')
        ON CONFLICT (ship_symbol) DO UPDATE
        SET agent_name = EXCLUDED.agent_name,
            faction_symbol = EXCLUDED.faction_symbol,
            ship_role = EXCLUDED.ship_role,
            cargo_capacity = EXCLUDED.cargo_capacity,
            cargo_in_use = EXCLUDED.cargo_in_use,
            fuel_capacity = EXCLUDED.fuel_capacity,
            fuel_current = EXCLUDED.fuel_current,
            mount_symbols = EXCLUDED.mount_symbols,
            module_symbols = EXCLUDED.module_symbols,
            last_updated = NOW() at time zone 'utc';

            """
    if ship.dirty or ship.fuel_dirty or ship.cargo_dirty:
        modules = [m if isinstance(m, str) else m.symbol for m in ship.modules]
        mounts = [m if isinstance(m, str) else m.symbol for m in ship.mounts]
        resp = try_execute_upsert(
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
                mounts,
                modules,
            ),
            connection,
        )
        if not resp:
            return resp
    if ship.mounts_dirty or ship.dirty:
        resp = _upsert_ship_mounts(ship, connection)
        if not resp:
            logging.warning("Failed to upsert ship mounts because %s", resp.error)
            return resp

    if ship.cargo_dirty or ship.dirty:
        resp = _upsert_ship_cargo(ship, connection)
        if not resp:
            logging.warning("Failed to upsert ship cargo because %s", resp.error)
            return resp

    if ship.nav_dirty or ship.dirty:
        resp = _upsert_ship_nav(ship, connection)
        if not resp:
            logging.warning("Failed to upsert ship nav because %s", resp.error)
            return resp
    if ship.dirty:
        resp = _upsert_ship_frame(ship, connection)
        if not resp:
            logging.warning("Failed to upsert ship frame because %s", resp.error)
            return resp
    if ship.cooldown_dirty:
        resp = _upsert_ship_cooldown(ship, connection)
        if not resp:
            logging.warning("Failed to upsert ship cooldown because %s", resp.error)
            return resp
    ship.mark_clean()
    return resp


def _upsert_ship_mounts(ship: Ship, connection):
    sql = """insert into ships (ship_symbol, mount_symbols)
    values (%s, %s) ON CONFLICT (ship_symbol) DO UPDATE
    SET mount_symbols = EXCLUDED.mount_symbols;"""
    values = (ship.name, [m.symbol for m in ship.mounts])
    resp = try_execute_upsert(sql, values, connection)
    return resp


def _upsert_ship_nav(ship: Ship, connection):
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
    resp = try_execute_upsert(sql, values, connection)
    return resp


def _upsert_ship_frame(ship: Ship, connection):
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
    resp = try_execute_upsert(sql, values, connection)
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
    resp = try_execute_upsert(sql, values, connection)
    return resp


def _upsert_ship_cooldown(ship: Ship, connection):
    sql = """insert into ship_cooldowns  (ship_symbol, total_seconds, expiration)
    values (%s, %s, %s) ON CONFLICT (ship_symbol, expiration) DO NOTHING;"""
    values = (ship.name, ship._cooldown_length, ship._cooldown_expiration)
    resp = try_execute_upsert(sql, values, connection)
    return resp


def _upsert_ship_cargo(ship: Ship, connection):
    sql = """
    
    INSERT INTO SHIP_CARGO (ship_symbol, trade_symbol, quantity)
    VALUES (%s, %s, %s) ON CONFLICT (ship_symbol, trade_symbol) DO UPDATE
    SET quantity = EXCLUDED.quantity;
    """

    values = [(ship.name, t.symbol, t.units) for t in ship.cargo_inventory]
    for value in values:
        resp = try_execute_upsert(sql, value, connection)
        if not resp:
            return resp
    if len(values) > 0:
        sql = """ 
delete from ship_cargo where ship_symbol = %s and trade_symbol not in %s;"""
        values = (ship.name, tuple([t.symbol for t in ship.cargo_inventory]))
        resp = try_execute_upsert(sql, values, connection)
    else:
        sql = "delete from ship_cargo where ship_symbol = %s;"
        resp = try_execute_upsert(sql, (ship.name,), connection)
    return resp
    # not implemented yet
    pass
