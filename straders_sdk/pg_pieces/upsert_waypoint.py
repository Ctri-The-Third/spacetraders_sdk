import psycopg2


from ..models import Waypoint, WaypointTrait
from ..utils import try_execute_upsert


def _upsert_waypoint(waypoint: Waypoint):
    checked = (
        len(waypoint.traits) > 0 or waypoint.is_charted
    )  # a system waypoint will not return any traits. Even if it's uncharted, we've checked it.
    # a waypoint with exactly zero traits that has been checked is a jump gate, and will have a chart
    # if it'snot been charted, then it's UNCHARTED and the first condition gets it.
    sql = """INSERT INTO waypoints (waypoint_symbol, type, system_symbol, x, y, modifiers, under_construction, checked)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (waypoint_symbol) DO UPDATE
                    SET checked = EXCLUDED.checked
                , modifiers = EXCLUDED.modifiers
                , under_construction = EXCLUDED.under_construction"""
    try_execute_upsert(
        sql,
        (
            waypoint.symbol,
            waypoint.type,
            waypoint.system_symbol,
            waypoint.x,
            waypoint.y,
            waypoint.modifiers,
            waypoint.under_construction,
            checked,
        ),
    )

    for trait in waypoint.traits:
        sql = """INSERT INTO waypoint_traits (waypoint_symbol, trait_symbol, name, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (waypoint_symbol, trait_symbol) DO nothing;"""
        try_execute_upsert(
            sql,
            (
                waypoint.symbol,
                trait.symbol,
                trait.name,
                trait.description,
            ),
        )
    if waypoint.is_charted and len(waypoint.chart) > 0:
        sql = """INSERT into waypoint_charts 
            ( waypoint_symbol, submitted_by, submitted_on)
            VALUES (%s, %s, %s)
            ON CONFLICT do nothing"""
        try_execute_upsert(
            sql,
            (
                waypoint.symbol,
                waypoint.chart["submittedBy"],
                waypoint.chart["submittedOn"],
            ),
        )
