import psycopg2


from ..models import System
from ..pg_pieces.upsert_waypoint import _upsert_waypoint
from ..utils import try_execute_upsert


def _upsert_system(connection, system: System):
    try:
        connection.autocommit = False
        sql = """INSERT INTO systems (system_symbol, type, sector_symbol, x, y)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (system_symbol) DO UPDATE
                    SET type = %s,  sector_symbol = %s, x = %s, y = %s"""
        try_execute_upsert(
            connection,
            sql,
            (
                system.symbol,
                system.system_type,
                system.sector_symbol,
                system.x,
                system.y,
                system.system_type,
                system.sector_symbol,
                system.x,
                system.y,
            ),
        )

    except Exception as err:
        print(err)

    for waypoint in system.waypoints:
        _upsert_waypoint(connection, waypoint)
    connection.commit()
    connection.autocommit = True
