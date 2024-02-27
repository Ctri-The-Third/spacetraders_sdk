from ..models_misc import ConstructionSite, ConstructionSiteMaterial
from ..resp_local_resp import LocalSpaceTradersRespose
import logging
import datetime
from ..utils import try_execute_upsert, try_execute_select


def _upsert_construction_site(construction_site: ConstructionSite, connection):
    sql = """INSERT INTO public.construction_sites(
	waypoint_symbol, is_complete)
	VALUES (%s, %s) ON CONFLICT (waypoint_symbol) DO UPDATE SET is_complete = EXCLUDED.is_complete
    ;"""

    material_sql = """INSERT INTO public.construction_site_materials(
	waypoint_symbol, trade_symbol, required, fulfilled)
	VALUES (%s, %s, %s, %s)
    ON CONFLICT (waypoint_symbol, trade_symbol) DO UPDATE SET required = EXCLUDED.required, fulfilled = EXCLUDED.fulfilled
    ;"""

    resp = try_execute_upsert(
        sql,
        (construction_site.waypoint_symbol, construction_site.is_complete),
        connection,
    )
    if not resp:
        return resp
    for material in construction_site.materials:
        resp = try_execute_upsert(
            material_sql,
            (
                construction_site.waypoint_symbol,
                material.symbol,
                material.required,
                material.fulfilled,
            ),
            connection,
        )
        if not resp:
            return resp

    return LocalSpaceTradersRespose(
        None, 0, None, "pg_pieces.construction_sites._upsert_construction_site"
    )


def select_construction_site_one(
    waypoint_symbol: str, connection
) -> ConstructionSite or "SpaceTradersResponse":
    sql = """select waypoint_symbol, is_complete from construction_sites where waypoint_symbol = %s"""

    material_sql = """select  trade_symbol, required, fulfilled from construction_site_materials where waypoint_symbol = %s"""

    resp = try_execute_select(sql, (waypoint_symbol,), connection)
    if not resp:
        return resp
    construction_site = ConstructionSite(resp[0][0], [], resp[0][1])
    resp = try_execute_select(material_sql, (waypoint_symbol,), connection)
    if not resp:
        return resp
    for material in resp:
        construction_site.materials.append(ConstructionSiteMaterial(*material))
    return construction_site
