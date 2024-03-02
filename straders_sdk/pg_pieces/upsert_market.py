from ..models_misc import Market, MarketTradeGoodListing, Waypoint
import psycopg2
import logging
from datetime import datetime
from ..utils import waypoint_to_system
from ..utils import try_execute_select, try_execute_upsert
from ..resp_local_resp import LocalSpaceTradersRespose


def _upsert_market(market: Market, connection):
    system_symbol = waypoint_to_system(market.symbol)
    sql = """INSERT INTO public.market(
symbol, system_symbol)
VALUES (%s, %s) 
ON CONFLICT (symbol) DO NOTHING;"""

    resp = try_execute_upsert(sql, (market.symbol, system_symbol), connection)
    if not resp:
        return resp
    sql = """INSERT INTO public.market_tradegoods(
        market_symbol, trade_symbol, type, name, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (market_symbol, trade_symbol) DO NOTHING"""
    if not resp:
        return resp
    for trade_good in market.exports:
        resp = try_execute_upsert(
            sql,
            (
                market.symbol,
                trade_good.symbol,
                "EXPORT",
                trade_good.name,
                trade_good.description,
            ),
            connection,
        )
        if not resp:
            return resp
    for trade_good in market.imports:
        resp = try_execute_upsert(
            sql,
            (
                market.symbol,
                trade_good.symbol,
                "IMPORT",
                trade_good.name,
                trade_good.description,
            ),
            connection,
        )
        if not resp:
            return resp
    for trade_good in market.exchange:
        resp = try_execute_upsert(
            sql,
            (
                market.symbol,
                trade_good.symbol,
                "EXCHANGE",
                trade_good.name,
                trade_good.description,
            ),
            connection,
        )
        if not resp:
            return resp
    # if market.exchange is not None and len(market.exchange) > 0:

    #    for trade_good in market.exchange:
    #        # cursor.execute(sql, (market.symbol, trade_good.symbol, trade_good.trade_volume
    #        pass

    if market.listings:
        sql = """INSERT INTO public.market_tradegood_listings
            ( market_symbol, trade_symbol, supply,  market_depth, purchase_price, sell_price, last_updated, type, activity )
            VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s )
            ON CONFLICT (market_symbol, trade_symbol) DO UPDATE
                    SET supply = EXCLUDED.supply
                    , purchase_price = EXCLUDED.purchase_price
                    , sell_price = EXCLUDED.sell_price
                    , last_updated = EXCLUDED.last_updated
                    , type = EXCLUDED.type
                    , activity = EXCLUDED.activity
                    , market_depth = EXCLUDED.market_depth"""
        for listing in market.listings:
            listing: MarketTradeGoodListing
            resp = try_execute_upsert(
                sql,
                (
                    market.symbol,
                    listing.symbol,
                    listing.supply,
                    listing.trade_volume,
                    listing.purchase_price,
                    listing.sell_price,
                    listing.recorded_ts,
                    listing.type,
                    listing.activity,
                ),
                connection,
            )
            if not resp:
                return resp

    return LocalSpaceTradersRespose(None, None, None, url=f"{__name__}._upsert_market")
