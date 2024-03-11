from ..resp_local_resp import LocalSpaceTradersRespose
from ..models_ship import Ship, ShipFrame, ShipNav, ShipInventory
from ..models_misc import RouteNode
from ..client_interface import SpaceTradersClient
from ..models_misc import ShipRequirements
from ..utils import try_execute_select, try_execute_upsert


def _select_ships(agent_name, db_client: SpaceTradersClient):
    sql = """select s.ship_symbol, s.agent_name, s.faction_symbol, s.ship_role, s.cargo_capacity, s.cargo_in_use
                , n.waypoint_symbol, n.departure_time, n.arrival_time, n.o_waypoint_symbol, n.d_waypoint_symbol, n.flight_status, n.flight_mode
                , sfl.condition, sfl.integrity --13
                , sf.frame_symbol, sf.name, sf.description, sf.module_slots, sf.mount_points, sf.fuel_capacity, sf.required_power, sf.required_crew, sf.required_slots
                , s.fuel_capacity, s.fuel_current --25  
                , sc.expiration, sc.total_seconds --27
                , n.o_waypoint_symbol, o.type, o.system_symbol, o.x, o.y --32
				, n.d_waypoint_symbol, d.type, n.system_symbol, d.x, d.y --38
                , s.mount_symbols, s.module_symbols --40                

                

                from ships s join ship_nav n on s.ship_symbol = n.ship_symbol
                left join ship_frame_links sfl on s.ship_symbol = sfl.ship_symbol
                left join ship_frames sf on sf.frame_symbol = sfl.frame_symbol
                left join ship_cooldown sc on s.ship_symbol = sc.ship_symbol
                left join waypoints o on n.o_waypoint_symbol = o.waypoint_symbol
				left join waypoints d on n.d_waypoint_symbol = d.waypoint_symbol

                where s.agent_name = %s
                order by s.ship_symbol
                """
    ships = _select_some_ships(db_client, sql, (agent_name,))
    if not ships:
        return {}
    ships = _expand_ships_with_inventory(db_client, ships, agent_name)
    return ships


def _select_ship_one(ship_symbol: str, db_client: SpaceTradersClient):
    sql = """select s.ship_symbol, s.agent_name, s.faction_symbol, s.ship_role, s.cargo_capacity, s.cargo_in_use
                , n.waypoint_symbol, n.departure_time, n.arrival_time, n.o_waypoint_symbol, n.d_waypoint_symbol, n.flight_status, n.flight_mode
                , sfl.condition, sfl.integrity --13
                , sf.frame_symbol, sf.name, sf.description, sf.module_slots, sf.mount_points, sf.fuel_capacity, sf.required_power, sf.required_crew, sf.required_slots
                , s.fuel_capacity, s.fuel_current --25  
                , sc.expiration, sc.total_seconds --27
                , n.o_waypoint_symbol, o.type, o.system_symbol, o.x, o.y --32
				, n.d_waypoint_symbol, d.type, n.system_symbol, d.x, d.y --38
                , s.mount_symbols, s.module_symbols --40

                from ships s join ship_nav n on s.ship_symbol = n.ship_symbol
                left join ship_frame_links sfl on s.ship_symbol = sfl.ship_symbol
                left join ship_frames sf on sf.frame_symbol = sfl.frame_symbol
                left join ship_cooldown sc on s.ship_symbol = sc.ship_symbol
                left join waypoints o on n.o_waypoint_symbol = o.waypoint_symbol
				left join waypoints d on n.d_waypoint_symbol = d.waypoint_symbol

                where s.ship_symbol = %s
                """
    ships = _select_some_ships(db_client, sql, (ship_symbol,))
    if not ships:
        return {}
    for ship_symbol, ship in ships.items():
        ship = _expand_ship_with_inventory(db_client, ship)
    return ships


def _expand_ship_with_inventory(db_client: SpaceTradersClient, ship: Ship):
    sql = """
        select sc.ship_Symbol, agent_name, trade_symbol, quantity::integer from ship_cargo sc join ships s 
        on sc.ship_symbol = s.ship_symbol
        where sc.ship_symbol = %s
        order by 1, 2 """

    rows = try_execute_select(sql, (ship.name,), db_client.connection)
    for row in rows:
        trade_symbol = row[2]
        units = row[3]
        ship.cargo_inventory.append(ShipInventory(trade_symbol, "", "", units))
    return ship


def _expand_ships_with_inventory(
    db_client: SpaceTradersClient, ships: dict, agent_name: str
):
    sql = """
    select sc.ship_Symbol, agent_name, trade_symbol, quantity::integer from ship_cargo sc join ships s 
        on sc.ship_symbol = s.ship_symbol
        where agent_name = %s
        order by 1, 2 """
    rows = try_execute_select(sql, (agent_name,), db_client.connection)
    for row in rows:
        trade_symbol = row[2]
        units = row[3]
        ship = ships.get(row[0], None)
        if ship:
            ship: Ship
            ship.cargo_inventory.append(ShipInventory(trade_symbol, "", "", units))
    return ships


def _select_some_ships(db_client: SpaceTradersClient, sql, params):
    try:
        rows = try_execute_select(sql, params, db_client.connection)
        if not rows:
            return rows
        ships = {}
        for row in rows:
            ship = Ship()
            ship.name = row[0]
            ship.faction = row[2]
            ship.role = row[3]
            ship.cargo_capacity = row[4]
            ship.cargo_units_used = row[5]
            ship.cargo_inventory = []
            # , 6: n.waypoint_symbol, n.departure_time, n.arrival_time, n.origin_waypoint, n.destination_waypoint, n.flight_status, n.flight_mode

            ship.nav = _nav_from_row(row)
            ship.frame = _frame_from_row(row)
            ship.fuel_capacity = row[24]
            ship.fuel_current = row[25]
            ship._cooldown_expiration = row[26]
            ship._cooldown_length = row[27]
            ship.mounts = row[38]
            ship.modules = row[39]
            ships[ship.name] = ship
            ship.mark_clean()

        return ships
    except Exception as err:
        return LocalSpaceTradersRespose(
            error=err,
            status_code=0,
            error_code=0,
            url=f"select_ship._select_ship",
        )


def _nav_from_row(row) -> ShipNav:
    """
    expected:
                s.ship_symbol, s.agent_name, s.faction_symbol, s.ship_role, s.cargo_capacity, s.cargo_in_use -- 6
                , n.waypoint_symbol, n.departure_time, n.arrival_time, n.o_waypoint_symbol, n.d_waypoint_symbol, n.flight_status, n.flight_mode
                , sfl.condition, sfl.integrity --13
                , sf.frame_symbol, sf.name, sf.description, sf.module_slots, sf.mount_points, sf.fuel_capacity, sf.required_power, sf.required_crew, sf.required_slots
                , s.fuel_capacity, s.fuel_current --25
                , sc.expiration, sc.total_seconds --27
                , n.o_waypoint_symbol, o.type, o.system_symbol, o.x, o.y --32
                 , n.d_waypoint_symbol, d.type, n.system_symbol, d.x, d.y --38
                , s.mount_symbols, s.module_symbols --40

    """

    return_obj = ShipNav(
        row[35],
        row[6],
        RouteNode(
            symbol=row[33],
            type=row[35],
            systemSymbol=row[36],
            x=row[37],
            y=row[38],
        ),
        RouteNode(
            symbol=row[10],
            type=row[33],
            systemSymbol=row[34],
            x=row[35],
            y=row[36],
        ),
        arrival_time=row[8],
        departure_time=row[7],
        status=row[11],
        flight_mode=row[12],
    )
    # SHIP NAV ENDS

    return return_obj


def _frame_from_row(row) -> ShipFrame:
    """
    expected:
                s.ship_symbol, s.agent_name, s.faction_symbol, s.ship_role, s.cargo_capacity, s.cargo_in_use -- 6
                , n.waypoint_symbol, n.departure_time, n.arrival_time, n.o_waypoint_symbol, n.d_waypoint_symbol, n.flight_status, n.flight_mode
                , sfl.condition, sfl.integrity --13
                , sf.frame_symbol, sf.name, sf.description, sf.module_slots, sf.mount_points, sf.fuel_capacity, sf.required_power, sf.required_crew, sf.required_slots
                , s.fuel_capacity, s.fuel_current --25
                , sc.expiration, sc.total_seconds --27
                , n.o_waypoint_symbol, o.type, o.system_symbol, o.x, o.y --32
                 , n.d_waypoint_symbol, d.type, n.system_symbol, d.x, d.y --38
                , s.mount_symbols, s.module_symbols --40
    """

    ##crew moduels power
    reqiurements = ShipRequirements(row[21], row[22], row[23])
    return_obj = ShipFrame(
        row[15],
        row[16],
        row[17],
        row[18],
        row[19],
        row[20],
        float(row[13]),
        float(row[14]),
        reqiurements,
    )

    return return_obj
