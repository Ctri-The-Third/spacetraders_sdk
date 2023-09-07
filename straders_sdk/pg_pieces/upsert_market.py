from ..models import Market, MarketTradeGoodListing, Waypoint
import psycopg2
import logging
from datetime import datetime
from ..utils import waypoint_slicer
from ..utils import try_execute_select, try_execute_upsert

# from psycopg2 import connection


def _upsert_market(connection, market: Market):
    system_symbol = waypoint_slicer(market.symbol)
    sql = """INSERT INTO public.market(
symbol, system_symbol)
VALUES (%s, %s) 
ON CONFLICT (symbol) DO NOTHING;"""

    resp = try_execute_upsert(connection, sql, (market.symbol, system_symbol))
    if not resp:
        return resp
    sql = """INSERT INTO public.market_tradegood(
        market_waypoint, symbol, buy_or_sell, name, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (market_waypoint, symbol) DO NOTHING"""

    for trade_good in market.exports:
        try_execute_upsert(
            connection,
            sql,
            (
                market.symbol,
                trade_good.symbol,
                "sell",
                trade_good.name,
                trade_good.description,
            ),
        )
    for trade_good in market.imports:
        try_execute_upsert(
            connection,
            sql,
            (
                market.symbol,
                trade_good.symbol,
                "buy",
                trade_good.name,
                trade_good.description,
            ),
        )
    for trade_good in market.exchange:
        try_execute_upsert(
            connection,
            sql,
            (
                market.symbol,
                trade_good.symbol,
                "exchange",
                trade_good.name,
                trade_good.description,
            ),
        )
    # if market.exchange is not None and len(market.exchange) > 0:

    #    for trade_good in market.exchange:
    #        # cursor.execute(sql, (market.symbol, trade_good.symbol, trade_good.trade_volume
    #        pass

    if market.listings:
        sql = """INSERT INTO public.market_tradegood_listings
            ( market_symbol, trade_symbol, supply,  market_depth, purchase_price, sell_price, last_updated )
            VALUES ( %s, %s, %s, %s, %s, %s, %s )
            ON CONFLICT (market_symbol, trade_symbol) DO UPDATE
                    SET supply = EXCLUDED.supply
                    , purchase_price = EXCLUDED.purchase_price
                    , sell_price = EXCLUDED.sell_price
                    , last_updated = EXCLUDED.last_updated"""
        for listing in market.listings:
            listing: MarketTradeGoodListing
            resp = try_execute_upsert(
                connection,
                sql,
                (
                    market.symbol,
                    listing.symbol,
                    listing.supply,
                    listing.trade_volume,
                    listing.purchase,
                    listing.sell_price,
                    listing.recorded_ts,
                ),
            )
