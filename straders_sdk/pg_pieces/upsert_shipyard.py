from ..models_misc import Shipyard, ShipyardShip
import psycopg2
import logging
from ..utils import try_execute_upsert


def _upsert_shipyard(shipyard: Shipyard, connection):
    if len(shipyard.ships) > 0:
        sql = """INSERT INTO public.shipyard_types(
        shipyard_symbol, ship_type, ship_cost, last_updated)
        VALUES (%s, %s, %s, now() at time zone 'utc')
        ON CONFLICT (shipyard_symbol, ship_type) DO UPDATE
        SET ship_cost = EXCLUDED.ship_cost,
        last_updated = now() at time zone 'utc';"""
        for ship_type in shipyard.ship_types:
            ship_cost = None
            ship_details = shipyard.ships.get(ship_type, None)
            if ship_details:
                ship_cost = ship_details.purchase_price
            resp = try_execute_upsert(
                sql, (shipyard.waypoint, ship_type, ship_cost), connection
            )
            if not resp:
                return resp

    else:
        try:
            sql = """INSERT INTO public.shipyard_types(
        shipyard_symbol, ship_type, last_updated)
        VALUES (%s, %s, now() at time zone 'utc')
        ON CONFLICT (shipyard_symbol, ship_type) DO NOTHING;"""
            for ship_type in shipyard.ship_types:
                resp = try_execute_upsert(
                    sql, (shipyard.waypoint, ship_type), connection
                )
                if not resp:
                    return resp
        except Exception as err:
            logging.error(err)
