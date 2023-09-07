from ..models import Shipyard, ShipyardShip
import psycopg2
import logging


def _upsert_shipyard(connection, shipyard: Shipyard):
    if len(shipyard.ships) > 0:
        try:
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
                connection.cursor().execute(
                    sql, (shipyard.waypoint, ship_type, ship_cost)
                )

            connection.commit()
        except Exception as err:
            logging.error(err)
    else:
        try:
            sql = """INSERT INTO public.shipyard_types(
        shipyard_symbol, ship_type, last_updated)
        VALUES (%s, %s, now() at time zone 'utc')
        ON CONFLICT (shipyard_symbol, ship_type) DO NOTHING;"""
            for ship_type in shipyard.ship_types:
                connection.cursor().execute(sql, (shipyard.waypoint, ship_type))
        except Exception as err:
            logging.error(err)
