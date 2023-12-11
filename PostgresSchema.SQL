--psql -U <username> -d <database_name> -f <file_name>.sql

set search_path = public;


-- DON'T FORGET THE SHIPYARD TYPE TO SHIP LINK THING
/* SELECT unnest(ARRAY['SATELLITEFRAME_PROBE'::text,'HAULERFRAME_LIGHT_FREIGHTER'::text, 'EXCAVATORFRAME_MINER'::text, 'COMMANDFRAME_FRIGATE'::text, 'EXCAVATORFRAME_DRONE'::text, 'SATELLITEFRAME_PROBE'::text, 'REFINERYFRAME_HEAVY_FREIGHTER'::text]) AS ship_roleframe,
    unnest(ARRAY['SHIP_PROBE'::text,'SHIP_LIGHT_FREIGHTER'::text, 'SHIP_ORE_HOUND'::text, 'SHIP_COMMAND_FRIGATE'::text, 'SHIP_MINING_DRONE'::text, 'SHIP_PROBE'::text, 'SHIP_REFINING_FREIGHTER'::text ]) AS shipyard_type
  WITH DATA;
*/
-------------------------------------------
--
-- PostgreSQL database dump
--

-- Dumped from database version 13.11 (Debian 13.11-0+deb11u1)
-- Dumped by pg_dump version 15.3

-- Started on 2023-12-11 15:54:12

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: spacetraders
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO spacetraders;

--
-- TOC entry 2 (class 3079 OID 56145)
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA public;


--
-- TOC entry 3419 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 201 (class 1259 OID 40386)
-- Name: agents; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.agents (
    agent_symbol text NOT NULL,
    headquarters text,
    credits integer,
    starting_faction text,
    ship_count integer,
    last_updated timestamp without time zone
);


ALTER TABLE public.agents OWNER TO spacetraders;

--
-- TOC entry 205 (class 1259 OID 40414)
-- Name: logging; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.logging (
    event_name text,
    event_timestamp timestamp without time zone NOT NULL,
    agent_name text,
    ship_symbol text NOT NULL,
    session_id text,
    endpoint_name text,
    new_credits integer,
    status_code integer,
    error_code integer,
    event_params jsonb,
    duration_seconds numeric
);


ALTER TABLE public.logging OWNER TO spacetraders;

--
-- TOC entry 203 (class 1259 OID 40398)
-- Name: transactions; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.transactions (
    waypoint_symbol text,
    ship_symbol text NOT NULL,
    trade_symbol text,
    type text,
    units integer,
    price_per_unit integer,
    total_price numeric,
    session_id text,
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.transactions OWNER TO spacetraders;

--
-- TOC entry 239 (class 1259 OID 40974)
-- Name: mat_session_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: spacetraders
--

CREATE MATERIALIZED VIEW public.mat_session_stats AS
 WITH sessions_and_requests AS (
         SELECT logging.session_id,
            min(logging.event_timestamp) AS session_start,
            max(logging.event_timestamp) AS session_end,
            count(
                CASE
                    WHEN ((logging.status_code > 0) AND (logging.status_code <> ALL (ARRAY[404, 429, 500]))) THEN 1
                    ELSE NULL::integer
                END) AS requests,
            count(
                CASE
                    WHEN (logging.status_code = 429) THEN 1
                    ELSE NULL::integer
                END) AS delayed_requests
           FROM public.logging
          WHERE (logging.event_timestamp >= (now() - '3 days'::interval))
          GROUP BY logging.session_id
        ), sessions_and_earnings AS (
         SELECT t.session_id,
            sum(t.total_price) AS earnings
           FROM public.transactions t
          WHERE ((t.type = 'SELL'::text) AND (t."timestamp" >= (now() - '3 days'::interval)))
          GROUP BY t.session_id
        ), sessions_and_ship_symbols AS (
         SELECT DISTINCT logging.ship_symbol,
            logging.session_id
           FROM public.logging
          WHERE (logging.ship_symbol <> 'GLOBAL'::text)
        ), sessions_and_behaviours AS (
         SELECT l.session_id,
            (l.event_params ->> 'script_name'::text) AS behaviour_id
           FROM public.logging l
          WHERE (l.event_name = 'BEGIN_BEHAVIOUR_SCRIPT'::text)
        )
 SELECT sas.ship_symbol,
    sar.session_start,
    sar.session_id,
    COALESCE(sab.behaviour_id, 'BEHAVIOUR_NOT_RECORDED'::text) AS behaviour_id,
    COALESCE(ear.earnings, (0)::numeric) AS earnings,
    sar.requests,
    sar.delayed_requests,
    (COALESCE(ear.earnings, (0)::numeric) / (
        CASE
            WHEN (sar.requests = 0) THEN (1)::bigint
            ELSE sar.requests
        END)::numeric) AS cpr
   FROM (((sessions_and_requests sar
     LEFT JOIN sessions_and_earnings ear ON ((ear.session_id = sar.session_id)))
     LEFT JOIN sessions_and_ship_symbols sas ON ((sar.session_id = sas.session_id)))
     LEFT JOIN sessions_and_behaviours sab ON ((sar.session_id = sab.session_id)))
  ORDER BY sar.session_start DESC
  WITH NO DATA;


ALTER TABLE public.mat_session_stats OWNER TO spacetraders;

--
-- TOC entry 202 (class 1259 OID 40392)
-- Name: ships; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ships (
    ship_symbol text NOT NULL,
    agent_name text,
    faction_symbol text,
    ship_role text,
    cargo_capacity integer,
    cargo_in_use integer,
    last_updated timestamp without time zone,
    fuel_capacity integer,
    fuel_current integer,
    mount_symbols text[],
    module_symbols text[]
);


ALTER TABLE public.ships OWNER TO spacetraders;

--
-- TOC entry 258 (class 1259 OID 77508)
-- Name: agent_credits_per_hour; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.agent_credits_per_hour AS
 WITH t_data AS (
         SELECT s.agent_name,
            sum(
                CASE
                    WHEN (t_1.type = 'SELL'::text) THEN t_1.total_price
                    ELSE
                    CASE
                        WHEN (t_1.type = 'PURCHASE'::text) THEN (t_1.total_price * ('-1'::integer)::numeric)
                        ELSE NULL::numeric
                    END
                END) AS credits_earned,
            date_trunc('hour'::text, t_1."timestamp") AS event_hour
           FROM ((public.transactions t_1
             JOIN public.ships s ON ((t_1.ship_symbol = s.ship_symbol)))
             JOIN public.agents a ON ((s.agent_name = a.agent_symbol)))
          GROUP BY s.agent_name, (date_trunc('hour'::text, t_1."timestamp"))
        ), l_data AS (
         SELECT s.agent_name,
            date_trunc('hour'::text, mss.session_start) AS event_hour,
            round((sum(mss.requests) / (60)::numeric), 2) AS rpm
           FROM (public.mat_session_stats mss
             JOIN public.ships s ON ((mss.ship_symbol = s.ship_symbol)))
          GROUP BY s.agent_name, (date_trunc('hour'::text, mss.session_start))
        )
 SELECT t.agent_name,
    t.credits_earned,
    l.rpm,
    t.event_hour
   FROM (t_data t
     LEFT JOIN l_data l ON (((t.agent_name = l.agent_name) AND (t.event_hour = l.event_hour))))
  ORDER BY t.event_hour DESC, t.agent_name;


ALTER TABLE public.agent_credits_per_hour OWNER TO spacetraders;

--
-- TOC entry 204 (class 1259 OID 40409)
-- Name: agent_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.agent_overview AS
 SELECT a.agent_symbol,
    a.credits,
    a.starting_faction,
    count(DISTINCT s.ship_symbol) AS ship_count,
    a.last_updated
   FROM (public.agents a
     JOIN public.ships s ON ((s.agent_name = a.agent_symbol)))
  GROUP BY a.agent_symbol, a.credits, a.starting_faction, a.last_updated
  ORDER BY a.last_updated DESC;


ALTER TABLE public.agent_overview OWNER TO spacetraders;

--
-- TOC entry 206 (class 1259 OID 40428)
-- Name: ship_behaviours; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_behaviours (
    ship_symbol text NOT NULL,
    behaviour_id text,
    locked_by text,
    locked_until timestamp without time zone,
    behaviour_params jsonb
);


ALTER TABLE public.ship_behaviours OWNER TO spacetraders;

--
-- TOC entry 240 (class 1259 OID 40982)
-- Name: behaviour_performance; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.behaviour_performance AS
 WITH data AS (
         SELECT date_trunc('hour'::text, mss.session_start) AS activity_window,
            s.ship_symbol,
            s.ship_role,
            sb.behaviour_id,
            sum(mss.earnings) AS earnings,
            sum(mss.requests) AS requests,
            count(*) AS sessions
           FROM ((public.mat_session_stats mss
             JOIN public.ships s ON ((mss.ship_symbol = s.ship_symbol)))
             JOIN public.ship_behaviours sb ON ((s.ship_symbol = sb.ship_symbol)))
          WHERE ((mss.session_start < date_trunc('hour'::text, now())) AND (mss.session_start >= (now() - '1 day'::interval)))
          GROUP BY (date_trunc('hour'::text, mss.session_start)), s.ship_symbol, s.ship_role, sb.behaviour_id
          ORDER BY (date_trunc('hour'::text, mss.session_start)) DESC, s.ship_symbol
        ), data_2 AS (
         SELECT data.activity_window,
            data.behaviour_id,
            sum(data.sessions) AS sessions,
            sum(data.earnings) AS earnings,
            sum(data.requests) AS requests,
            round((sum(data.earnings) / sum(data.requests)), 2) AS cpr,
            round((sum(data.earnings) / sum(data.sessions)), 2) AS bhvr_cph
           FROM data
          GROUP BY data.activity_window, data.behaviour_id
          ORDER BY data.activity_window DESC
        )
 SELECT data_2.activity_window,
    data_2.behaviour_id,
    data_2.sessions,
    data_2.earnings,
    data_2.requests,
    data_2.cpr,
    data_2.bhvr_cph
   FROM data_2
  WHERE (data_2.earnings > (0)::numeric);


ALTER TABLE public.behaviour_performance OWNER TO spacetraders;

--
-- TOC entry 207 (class 1259 OID 40439)
-- Name: contract_tradegoods; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.contract_tradegoods (
    contract_id text NOT NULL,
    trade_symbol text NOT NULL,
    destination_symbol text,
    units_required integer,
    units_fulfilled integer
);


ALTER TABLE public.contract_tradegoods OWNER TO spacetraders;

--
-- TOC entry 208 (class 1259 OID 40445)
-- Name: contracts; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.contracts (
    id text NOT NULL,
    faction_symbol text,
    type text,
    accepted boolean,
    fulfilled boolean,
    expiration timestamp without time zone,
    deadline timestamp without time zone,
    agent_symbol text,
    payment_upfront integer,
    payment_on_completion integer,
    offering_faction text
);


ALTER TABLE public.contracts OWNER TO spacetraders;

--
-- TOC entry 209 (class 1259 OID 40451)
-- Name: contracts_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.contracts_overview AS
 SELECT co.agent_symbol,
    ct.trade_symbol,
    round((((ct.units_fulfilled)::numeric / (ct.units_required)::numeric) * (100)::numeric), 2) AS progress,
    ct.units_required,
    ct.units_fulfilled,
    co.expiration,
    (co.payment_on_completion / ct.units_required) AS payment_per_item,
    co.fulfilled
   FROM (public.contracts co
     JOIN public.contract_tradegoods ct ON ((co.id = ct.contract_id)))
  WHERE (co.fulfilled = false);


ALTER TABLE public.contracts_overview OWNER TO spacetraders;

--
-- TOC entry 273 (class 1259 OID 84863)
-- Name: export_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.export_overview AS
SELECT
    NULL::text AS system_symbol,
    NULL::text AS market_symbol,
    NULL::text AS trade_symbol,
    NULL::text AS supply,
    NULL::text AS activity,
    NULL::integer AS purchase_price,
    NULL::integer AS sell_price,
    NULL::integer AS market_depth,
    NULL::bigint AS units_sold_recently,
    NULL::text[] AS requirements;


ALTER TABLE public.export_overview OWNER TO spacetraders;

--
-- TOC entry 251 (class 1259 OID 64900)
-- Name: extractions; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.extractions (
    ship_symbol text NOT NULL,
    session_id text,
    event_timestamp timestamp without time zone NOT NULL,
    waypoint_symbol text,
    survey_signature text,
    trade_symbol text,
    quantity integer
);


ALTER TABLE public.extractions OWNER TO spacetraders;

--
-- TOC entry 210 (class 1259 OID 40456)
-- Name: jump_gates; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.jump_gates (
    waypoint_symbol text NOT NULL,
    faction_symbol text,
    jump_range integer
);


ALTER TABLE public.jump_gates OWNER TO spacetraders;

--
-- TOC entry 237 (class 1259 OID 40828)
-- Name: jumpgate_connections; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.jumpgate_connections (
    s_waypoint_symbol text,
    s_system_symbol text NOT NULL,
    d_system_symbol text NOT NULL
);


ALTER TABLE public.jumpgate_connections OWNER TO spacetraders;

--
-- TOC entry 211 (class 1259 OID 40468)
-- Name: waypoint_charts; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.waypoint_charts (
    waypoint_symbol text NOT NULL,
    submitted_by text NOT NULL,
    submitted_on timestamp without time zone NOT NULL
);


ALTER TABLE public.waypoint_charts OWNER TO spacetraders;

--
-- TOC entry 212 (class 1259 OID 40474)
-- Name: waypoint_traits; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.waypoint_traits (
    waypoint_symbol text NOT NULL,
    trait_symbol text NOT NULL,
    name text,
    description text
);


ALTER TABLE public.waypoint_traits OWNER TO spacetraders;

--
-- TOC entry 213 (class 1259 OID 40480)
-- Name: waypoints; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.waypoints (
    waypoint_symbol text NOT NULL,
    type text NOT NULL,
    system_symbol text NOT NULL,
    x smallint NOT NULL,
    y smallint NOT NULL,
    checked boolean DEFAULT false NOT NULL,
    modifiers text[],
    under_construction boolean DEFAULT false NOT NULL
);


ALTER TABLE public.waypoints OWNER TO spacetraders;

--
-- TOC entry 214 (class 1259 OID 40487)
-- Name: jumpgates_scanned; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.jumpgates_scanned AS
 SELECT w.waypoint_symbol,
    (count(
        CASE
            WHEN (wt.trait_symbol = 'UNCHARTED'::text) THEN 1
            ELSE NULL::integer
        END) > 0) AS uncharted,
    (count(
        CASE
            WHEN (wc.waypoint_symbol IS NOT NULL) THEN 1
            ELSE NULL::integer
        END) > 0) AS charted,
    (count(
        CASE
            WHEN (jg.waypoint_symbol IS NOT NULL) THEN 1
            ELSE NULL::integer
        END) > 0) AS scanned
   FROM (((public.waypoints w
     LEFT JOIN public.waypoint_traits wt ON (((wt.waypoint_symbol = w.waypoint_symbol) AND (wt.trait_symbol = 'UNCHARTED'::text))))
     LEFT JOIN public.waypoint_charts wc ON ((wc.waypoint_symbol = w.waypoint_symbol)))
     LEFT JOIN public.jump_gates jg ON ((jg.waypoint_symbol = w.waypoint_symbol)))
  WHERE (w.type = 'JUMP_GATE'::text)
  GROUP BY w.waypoint_symbol;


ALTER TABLE public.jumpgates_scanned OWNER TO spacetraders;

--
-- TOC entry 215 (class 1259 OID 40492)
-- Name: jumpgates_scanned_progress; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.jumpgates_scanned_progress AS
 WITH data AS (
         SELECT count(*) AS total_gates,
            count(
                CASE
                    WHEN js.scanned THEN 1
                    ELSE NULL::integer
                END) AS scanned_gates,
            count(
                CASE
                    WHEN js.charted THEN 1
                    ELSE NULL::integer
                END) AS charted_gates
           FROM public.jumpgates_scanned js
        )
 SELECT 'charted jumpgates scanned'::text AS title,
    data.scanned_gates,
    data.charted_gates,
        CASE
            WHEN (data.scanned_gates > 0) THEN round((((data.charted_gates)::numeric / (data.scanned_gates)::numeric) * (100)::numeric), 2)
            ELSE NULL::numeric
        END AS progress
   FROM data;


ALTER TABLE public.jumpgates_scanned_progress OWNER TO spacetraders;

--
-- TOC entry 266 (class 1259 OID 79516)
-- Name: manufacture_relationships; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.manufacture_relationships (
    export_tradegood text NOT NULL,
    import_tradegoods text[] NOT NULL
);


ALTER TABLE public.manufacture_relationships OWNER TO spacetraders;

--
-- TOC entry 216 (class 1259 OID 40497)
-- Name: market; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.market (
    symbol text NOT NULL,
    system_symbol text
);


ALTER TABLE public.market OWNER TO spacetraders;

--
-- TOC entry 217 (class 1259 OID 40503)
-- Name: market_tradegood_listings; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.market_tradegood_listings (
    market_symbol text NOT NULL,
    trade_symbol text NOT NULL,
    supply text,
    purchase_price integer,
    sell_price integer,
    last_updated timestamp without time zone,
    market_depth integer,
    type text,
    activity text
);


ALTER TABLE public.market_tradegood_listings OWNER TO spacetraders;

--
-- TOC entry 272 (class 1259 OID 84842)
-- Name: market_changes; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.market_changes AS
 WITH "extract" AS (
         SELECT l.event_timestamp,
            (l.event_params ->> 'market_symbol'::text) AS market_symbol,
            (l.event_params ->> 'trade_symbol'::text) AS trade_symbol,
            (l.event_params ->> 'activity'::text) AS activity,
            (l.event_params ->> 'supply'::text) AS supply,
            ((l.event_params ->> 'purchase_price'::text))::numeric AS current_purchase_price,
            ((l.event_params ->> 'purchase_price_change'::text))::numeric AS cpp_change,
            ((l.event_params ->> 'sell_price'::text))::numeric AS current_sell_price,
            ((l.event_params ->> 'sell_price_change'::text))::numeric AS csp_change,
            ((l.event_params ->> 'trade_volume'::text))::numeric AS current_trade_volume,
            l.event_params
           FROM public.logging l
          WHERE (l.event_name = 'MARKET_CHANGES'::text)
          ORDER BY l.event_timestamp DESC
        )
 SELECT e.event_timestamp,
    e.market_symbol,
    e.trade_symbol,
    mtl.type,
    e.activity,
    e.supply,
    e.current_purchase_price,
    e.cpp_change,
    e.current_sell_price,
    e.csp_change,
    e.current_trade_volume
   FROM ("extract" e
     JOIN public.market_tradegood_listings mtl ON (((e.market_symbol = mtl.market_symbol) AND (e.trade_symbol = mtl.trade_symbol))));


ALTER TABLE public.market_changes OWNER TO spacetraders;

--
-- TOC entry 268 (class 1259 OID 79847)
-- Name: market_prices; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.market_prices AS
 SELECT mtl.trade_symbol,
    round(avg(mtl.purchase_price) FILTER (WHERE (mtl.type = 'EXPORT'::text)), 2) AS export_price,
    round(avg(mtl.sell_price) FILTER (WHERE (mtl.type = 'IMPORT'::text)), 2) AS import_price,
    round(avg(((mtl.purchase_price + mtl.sell_price) / 2)), 2) AS galactic_average
   FROM public.market_tradegood_listings mtl
  GROUP BY mtl.trade_symbol
  ORDER BY mtl.trade_symbol;


ALTER TABLE public.market_prices OWNER TO spacetraders;

--
-- TOC entry 218 (class 1259 OID 40513)
-- Name: market_tradegood; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.market_tradegood (
    market_waypoint text NOT NULL,
    symbol text NOT NULL,
    buy_or_sell text,
    name text,
    description text
);


ALTER TABLE public.market_tradegood OWNER TO spacetraders;

--
-- TOC entry 252 (class 1259 OID 65641)
-- Name: mat_session_behaviour_types; Type: MATERIALIZED VIEW; Schema: public; Owner: spacetraders
--

CREATE MATERIALIZED VIEW public.mat_session_behaviour_types AS
 SELECT l.session_id,
    l.event_timestamp AS session_start,
    l.ship_symbol,
    s.agent_name,
    (l.event_params ->> 'script_name'::text) AS behaviour_name
   FROM (public.logging l
     JOIN public.ships s ON ((l.ship_symbol = s.ship_symbol)))
  WHERE (l.event_name = 'BEGIN_BEHAVIOUR_SCRIPT'::text)
  WITH NO DATA;


ALTER TABLE public.mat_session_behaviour_types OWNER TO spacetraders;

--
-- TOC entry 260 (class 1259 OID 79002)
-- Name: mat_session_stats_2; Type: MATERIALIZED VIEW; Schema: public; Owner: spacetraders
--

CREATE MATERIALIZED VIEW public.mat_session_stats_2 AS
 WITH beginnings AS (
         SELECT l.session_id,
            l.event_timestamp AS session_start,
            l.ship_symbol,
            s.agent_name,
            (l.event_params ->> 'script_name'::text) AS behaviour_name
           FROM (public.logging l
             JOIN public.ships s ON ((l.ship_symbol = s.ship_symbol)))
          WHERE (l.event_name = 'BEGIN_BEHAVIOUR_SCRIPT'::text)
        ), ends AS (
         SELECT l.session_id,
            l.event_timestamp AS session_end
           FROM public.logging l
          WHERE (l.event_name = 'END_BEHAVIOUR_SCRIPT'::text)
        ), earnings AS (
         SELECT transactions.session_id,
            sum(
                CASE
                    WHEN (transactions.type = 'SELL'::text) THEN transactions.total_price
                    ELSE NULL::numeric
                END) AS earnings,
            sum(
                CASE
                    WHEN (transactions.type = 'PURCHASE'::text) THEN transactions.total_price
                    ELSE NULL::numeric
                END) AS losses,
            sum(
                CASE
                    WHEN (transactions.type = 'SELL'::text) THEN transactions.total_price
                    ELSE
                    CASE
                        WHEN (transactions.type = 'PURCHASE'::text) THEN (transactions.total_price * ('-1'::integer)::numeric)
                        ELSE NULL::numeric
                    END
                END) AS net_earnings
           FROM public.transactions
          GROUP BY transactions.session_id
        ), request_stats AS (
         SELECT l.session_id,
            count(
                CASE
                    WHEN ((l.status_code > 0) AND (l.status_code < 500) AND (l.status_code <> 429)) THEN 1
                    ELSE NULL::integer
                END) AS requests
           FROM public.logging l
          GROUP BY l.session_id
        )
 SELECT b.session_id,
    b.session_start,
    e.session_end,
    (e.session_end - b.session_start) AS duration,
    date_part('epoch'::text, (e.session_end - b.session_start)) AS duration_secs,
    b.ship_symbol,
    b.agent_name,
    b.behaviour_name,
    ea.earnings,
    ea.losses,
    ea.net_earnings,
    r.requests,
    (ea.net_earnings / (r.requests)::numeric) AS cpr,
    ((ea.net_earnings)::double precision / date_part('epoch'::text, (e.session_end - b.session_start))) AS cps
   FROM (((beginnings b
     LEFT JOIN ends e ON ((b.session_id = e.session_id)))
     LEFT JOIN earnings ea ON ((b.session_id = ea.session_id)))
     LEFT JOIN request_stats r ON ((b.session_id = r.session_id)))
  WHERE (e.session_id IS NOT NULL)
  ORDER BY (e.session_end - b.session_start) DESC
  WITH NO DATA;


ALTER TABLE public.mat_session_stats_2 OWNER TO spacetraders;

--
-- TOC entry 219 (class 1259 OID 40519)
-- Name: mat_shipyardtypes_to_ship; Type: MATERIALIZED VIEW; Schema: public; Owner: spacetraders
--

CREATE MATERIALIZED VIEW public.mat_shipyardtypes_to_ship AS
 SELECT unnest(ARRAY['SATELLITEFRAME_PROBE'::text, 'HAULERFRAME_LIGHT_FREIGHTER'::text, 'EXCAVATORFRAME_MINER'::text, 'COMMANDFRAME_FRIGATE'::text, 'EXCAVATORFRAME_DRONE'::text, 'SATELLITEFRAME_PROBE'::text, 'REFINERYFRAME_HEAVY_FREIGHTER'::text]) AS ship_roleframe,
    unnest(ARRAY['SHIP_PROBE'::text, 'SHIP_LIGHT_FREIGHTER'::text, 'SHIP_ORE_HOUND'::text, 'SHIP_COMMAND_FRIGATE'::text, 'SHIP_MINING_DRONE'::text, 'SHIP_PROBE'::text, 'SHIP_REFINING_FREIGHTER'::text]) AS shipyard_type
  WITH NO DATA;


ALTER TABLE public.mat_shipyardtypes_to_ship OWNER TO spacetraders;

--
-- TOC entry 267 (class 1259 OID 79610)
-- Name: mkt_export_and_imports; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_export_and_imports AS
 WITH unjoined_exports AS (
         SELECT mtl.trade_symbol,
            mtl.market_symbol,
            mtl.supply,
            mtl.activity,
            mtl.market_depth,
            mtl.purchase_price,
            mtl.sell_price,
            unnest(mr.import_tradegoods) AS required_import
           FROM (public.market_tradegood_listings mtl
             JOIN public.manufacture_relationships mr ON ((mtl.trade_symbol = mr.export_tradegood)))
          WHERE (mtl.type = 'EXPORT'::text)
        )
 SELECT w.system_symbol,
    e.trade_symbol,
    e.market_symbol,
    e.activity AS export_activity,
    e.supply AS export_supply,
    e.market_depth AS export_depth,
    i.trade_symbol AS required_trade_symbol,
    i.activity AS import_activity,
    i.supply AS import_supply,
    i.market_depth AS import_depth
   FROM ((unjoined_exports e
     LEFT JOIN public.market_tradegood_listings i ON (((i.trade_symbol = e.required_import) AND (e.market_symbol = i.market_symbol) AND (i.type = 'IMPORT'::text))))
     JOIN public.waypoints w ON ((e.market_symbol = w.waypoint_symbol)))
  ORDER BY w.system_symbol, e.trade_symbol, e.market_symbol;


ALTER TABLE public.mkt_export_and_imports OWNER TO spacetraders;

--
-- TOC entry 220 (class 1259 OID 40526)
-- Name: shipyard_types; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.shipyard_types (
    shipyard_symbol text NOT NULL,
    ship_type text NOT NULL,
    ship_cost integer,
    last_updated timestamp without time zone
);


ALTER TABLE public.shipyard_types OWNER TO spacetraders;

--
-- TOC entry 221 (class 1259 OID 40532)
-- Name: systems; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.systems (
    system_symbol text NOT NULL,
    sector_symbol text,
    type text,
    x integer,
    y integer
);


ALTER TABLE public.systems OWNER TO spacetraders;

--
-- TOC entry 222 (class 1259 OID 40538)
-- Name: mkt_shpyrds_systems_last_updated; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_shpyrds_systems_last_updated AS
 SELECT wt.waypoint_symbol,
    s.x,
    s.y,
    min(COALESCE(mtl.last_updated, st.last_updated, '1990-01-01 00:00:00'::timestamp without time zone)) AS last_updated
   FROM ((((public.waypoint_traits wt
     JOIN public.waypoints w ON ((w.waypoint_symbol = wt.waypoint_symbol)))
     JOIN public.systems s ON ((s.system_symbol = w.system_symbol)))
     LEFT JOIN public.market_tradegood_listings mtl ON ((mtl.market_symbol = wt.waypoint_symbol)))
     LEFT JOIN public.shipyard_types st ON ((st.shipyard_symbol = w.waypoint_symbol)))
  WHERE (wt.trait_symbol = ANY (ARRAY['MARKETPLACE'::text, 'SHIPYARD'::text]))
  GROUP BY wt.waypoint_symbol, s.x, s.y;


ALTER TABLE public.mkt_shpyrds_systems_last_updated OWNER TO spacetraders;

--
-- TOC entry 223 (class 1259 OID 40543)
-- Name: mkt_shpyrds_systems_last_updated_jumpgates; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_shpyrds_systems_last_updated_jumpgates AS
 SELECT w1.waypoint_symbol,
    msslu.x,
    msslu.y,
    msslu.last_updated,
    w2.waypoint_symbol AS jump_gate_waypoint
   FROM (((public.mkt_shpyrds_systems_last_updated msslu
     JOIN public.waypoints w1 ON ((w1.waypoint_symbol = msslu.waypoint_symbol)))
     JOIN public.waypoints w2 ON ((w1.system_symbol = w2.system_symbol)))
     JOIN public.jump_gates j ON ((w2.waypoint_symbol = j.waypoint_symbol)))
  WHERE ((w2.type = 'JUMP_GATE'::text) AND (w1.waypoint_symbol <> w2.waypoint_symbol));


ALTER TABLE public.mkt_shpyrds_systems_last_updated_jumpgates OWNER TO spacetraders;

--
-- TOC entry 244 (class 1259 OID 52623)
-- Name: mkt_shpyrds_systems_to_visit_first; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_shpyrds_systems_to_visit_first AS
 WITH valid_systems AS (
         SELECT DISTINCT jumpgate_connections.d_system_symbol AS system_symbol
           FROM public.jumpgate_connections
        ), unvisited_shipyards AS (
         SELECT DISTINCT w.system_symbol,
            ps.last_updated,
            (ps.last_updated IS NOT NULL) AS visited
           FROM (public.shipyard_types ps
             JOIN public.waypoints w ON ((w.waypoint_symbol = ps.shipyard_symbol)))
          WHERE ((ps.ship_type = ANY (ARRAY['SHIP_ORE_HOUND'::text, 'SHIP_REFINING_FREIGHTER'::text, 'SHIP_HEAVY_FREIGHTER'::text])) AND (ps.ship_cost IS NULL))
        ), unvisited_markets AS (
         SELECT DISTINCT w.system_symbol,
            mtl.last_updated,
            (mtl.last_updated IS NOT NULL) AS visited
           FROM ((public.market_tradegood mt
             LEFT JOIN public.market_tradegood_listings mtl ON (((mt.market_waypoint = mtl.market_symbol) AND (mt.symbol = mtl.trade_symbol))))
             JOIN public.waypoints w ON ((mt.market_waypoint = w.waypoint_symbol)))
          WHERE (((mt.symbol = ANY (ARRAY['IRON'::text, 'IRON_ORE'::text, 'COPPER'::text, 'COPPER_ORE'::text, 'ALUMINUM'::text, 'ALUMINUM_ORE'::text, 'SILVER'::text, 'SILVER_ORE'::text, 'GOLD'::text, 'GOLD_ORE'::text, 'PLATINUM'::text, 'PLATINUM_ORE'::text, 'URANITE'::text, 'URANITE_ORE'::text, 'MERITIUM'::text, 'MERITIUM_ORE'::text])) AND (mtl.last_updated IS NULL)) OR (mtl.last_updated <= (timezone('utc'::text, now()) - '1 day'::interval)))
          ORDER BY (mtl.last_updated IS NOT NULL), mtl.last_updated
        )
 SELECT us.system_symbol
   FROM (unvisited_shipyards us
     JOIN valid_systems vs ON ((us.system_symbol = vs.system_symbol)))
UNION
 SELECT um.system_symbol
   FROM (unvisited_markets um
     JOIN valid_systems vs ON ((um.system_symbol = vs.system_symbol)));


ALTER TABLE public.mkt_shpyrds_systems_to_visit_first OWNER TO spacetraders;

--
-- TOC entry 224 (class 1259 OID 40548)
-- Name: mkt_shpyrds_systems_visit_progress; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_shpyrds_systems_visit_progress AS
 WITH info AS (
         SELECT count(*) AS total,
            count(
                CASE
                    WHEN (mkt_shpyrds_systems_last_updated_jumpgates.last_updated > '1990-01-01 00:00:00'::timestamp without time zone) THEN 1
                    ELSE NULL::integer
                END) AS visited
           FROM public.mkt_shpyrds_systems_last_updated_jumpgates
        )
 SELECT 'Markets/Shipyards on gate network visited'::text AS "?column?",
    info.visited,
    info.total,
        CASE
            WHEN (info.total > 0) THEN round((((info.visited)::numeric / (info.total)::numeric) * (100)::numeric), 2)
            ELSE (0)::numeric
        END AS progress
   FROM info;


ALTER TABLE public.mkt_shpyrds_systems_visit_progress OWNER TO spacetraders;

--
-- TOC entry 225 (class 1259 OID 40553)
-- Name: mkt_shpyrds_waypoints_scanned; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_shpyrds_waypoints_scanned AS
 WITH data AS (
         SELECT wt.waypoint_symbol,
            wt.trait_symbol,
            count(st.*) AS ships_available,
            count(mt.*) AS goods_available
           FROM (((((public.waypoint_traits wt
             JOIN public.waypoints w1 ON ((wt.waypoint_symbol = w1.waypoint_symbol)))
             JOIN public.waypoints w2 ON (((w1.system_symbol = w2.system_symbol) AND (w1.waypoint_symbol <> w2.waypoint_symbol))))
             JOIN public.jump_gates jg ON ((jg.waypoint_symbol = w2.waypoint_symbol)))
             LEFT JOIN public.shipyard_types st ON ((st.shipyard_symbol = w1.waypoint_symbol)))
             LEFT JOIN public.market_tradegood mt ON ((mt.market_waypoint = w1.waypoint_symbol)))
          WHERE (wt.trait_symbol = ANY (ARRAY['MARKETPLACE'::text, 'SHIPYARD'::text]))
          GROUP BY wt.waypoint_symbol, wt.trait_symbol
        )
 SELECT data.waypoint_symbol,
    ((data.ships_available > 0) OR (data.goods_available > 0)) AS scanned
   FROM data;


ALTER TABLE public.mkt_shpyrds_waypoints_scanned OWNER TO spacetraders;

--
-- TOC entry 226 (class 1259 OID 40558)
-- Name: mkt_shpyrds_waypoints_scanned_progress; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.mkt_shpyrds_waypoints_scanned_progress AS
 SELECT 'Markets/ shipyards on gate network scanned'::text AS "?column?",
    count(
        CASE
            WHEN mkt_shpyrds_waypoints_scanned.scanned THEN 1
            ELSE NULL::integer
        END) AS scanned,
    count(*) AS total,
    round(((count(
        CASE
            WHEN mkt_shpyrds_waypoints_scanned.scanned THEN 1
            ELSE NULL::integer
        END))::numeric / ((
        CASE
            WHEN (count(*) > 0) THEN count(*)
            ELSE (1)::bigint
        END)::numeric * (100)::numeric)), 2) AS progress
   FROM public.mkt_shpyrds_waypoints_scanned;


ALTER TABLE public.mkt_shpyrds_waypoints_scanned_progress OWNER TO spacetraders;

--
-- TOC entry 250 (class 1259 OID 56229)
-- Name: pg_lock_monitor; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.pg_lock_monitor AS
 SELECT COALESCE(((blockingl.relation)::regclass)::text, blockingl.locktype) AS locked_item,
    (now() - blockeda.query_start) AS waiting_duration,
    blockeda.pid AS blocked_pid,
    blockeda.query AS blocked_query,
    blockedl.mode AS blocked_mode,
    blockinga.pid AS blocking_pid,
    blockinga.query AS blocking_query,
    blockingl.mode AS blocking_mode
   FROM (((pg_locks blockedl
     JOIN pg_stat_activity blockeda ON ((blockedl.pid = blockeda.pid)))
     JOIN pg_locks blockingl ON ((((blockingl.transactionid = blockedl.transactionid) OR ((blockingl.relation = blockedl.relation) AND (blockingl.locktype = blockedl.locktype))) AND (blockedl.pid <> blockingl.pid))))
     JOIN pg_stat_activity blockinga ON (((blockingl.pid = blockinga.pid) AND (blockinga.datid = blockeda.datid))))
  WHERE ((NOT blockedl.granted) AND (blockinga.datname = current_database()));


ALTER TABLE public.pg_lock_monitor OWNER TO spacetraders;

--
-- TOC entry 249 (class 1259 OID 56201)
-- Name: pg_stat_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.pg_stat_overview AS
 SELECT pg_stat_statements.calls,
    (pg_stat_statements.total_exec_time / (1000)::double precision) AS total_exec_time,
    (pg_stat_statements.min_exec_time / (1000)::double precision) AS min_exec_time,
    (pg_stat_statements.mean_exec_time / (1000)::double precision) AS mean_exec_time,
    pg_stat_statements.query
   FROM public.pg_stat_statements
  ORDER BY (pg_stat_statements.total_exec_time / (1000)::double precision) DESC;


ALTER TABLE public.pg_stat_overview OWNER TO spacetraders;

--
-- TOC entry 265 (class 1259 OID 79364)
-- Name: refinery_fuel; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.refinery_fuel AS
 SELECT w.waypoint_symbol,
    w.type,
    w.system_symbol,
    w.x,
    w.y,
    mtlf.supply AS i_supply,
    mtlh.supply AS e_supply,
    mtlf.market_depth AS i_depth,
    mtlh.market_depth AS e_depth,
    mtlf.activity AS i_activity,
    mtlh.activity AS e_activity,
    (count(*) = 2) AS is_refinery
   FROM (((public.market_tradegood mt
     JOIN public.waypoints w ON ((mt.market_waypoint = w.waypoint_symbol)))
     LEFT JOIN public.market_tradegood_listings mtlh ON (((mtlh.market_symbol = w.waypoint_symbol) AND (mtlh.trade_symbol = 'FUEL'::text))))
     LEFT JOIN public.market_tradegood_listings mtlf ON (((mtlf.market_symbol = w.waypoint_symbol) AND (mtlf.trade_symbol = 'HYDROCARBON'::text))))
  WHERE (((mt.symbol = 'FUEL'::text) AND (mt.buy_or_sell = 'sell'::text)) OR ((mt.symbol = 'HYDROCARBON'::text) AND (mt.buy_or_sell = 'buy'::text)))
  GROUP BY w.waypoint_symbol, w.type, w.system_symbol, w.x, w.y, mtlf.supply, mtlh.supply, mtlf.market_depth, mtlh.market_depth, mtlf.activity, mtlh.activity
 HAVING (count(*) = 2);


ALTER TABLE public.refinery_fuel OWNER TO spacetraders;

--
-- TOC entry 246 (class 1259 OID 54151)
-- Name: request_saturation_delays; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.request_saturation_delays AS
 SELECT date_trunc('minute'::text, l.event_timestamp) AS date_trunc,
    s.agent_name,
    round(avg(l.duration_seconds), 2) AS request_duration_secs
   FROM (public.logging l
     JOIN public.ships s ON ((l.ship_symbol = s.ship_symbol)))
  WHERE ((l.ship_symbol ~~* 'CTRI-%'::text) AND (l.duration_seconds IS NOT NULL) AND (l.event_timestamp >= (now() - '01:00:00'::interval)))
  GROUP BY (date_trunc('minute'::text, l.event_timestamp)), s.agent_name
  ORDER BY (date_trunc('minute'::text, l.event_timestamp)) DESC;


ALTER TABLE public.request_saturation_delays OWNER TO spacetraders;

--
-- TOC entry 242 (class 1259 OID 41012)
-- Name: session_stats_per_hour; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.session_stats_per_hour AS
 SELECT s.agent_name,
    date_trunc('hour'::text, mss.session_start) AS activity_time,
    count(DISTINCT mss.ship_symbol) AS active_ships,
    sum(mss.earnings) AS earnings,
    sum(mss.requests) AS requests,
    sum(mss.delayed_requests) AS delayed_requests,
    round((sum(mss.earnings) / sum(mss.requests)), 2) AS cpr,
    round((sum(mss.earnings) / (3600)::numeric), 2) AS total_cps,
    round((sum(mss.earnings) / (count(DISTINCT mss.ship_symbol))::numeric), 2) AS cphps
   FROM (public.mat_session_stats mss
     JOIN public.ships s ON ((mss.ship_symbol = s.ship_symbol)))
  WHERE ((mss.session_start < date_trunc('hour'::text, timezone('utc'::text, now()))) AND (date_trunc('hour'::text, mss.session_start) > (now() - '06:00:00'::interval)))
  GROUP BY s.agent_name, (date_trunc('hour'::text, mss.session_start))
  ORDER BY (date_trunc('hour'::text, mss.session_start)) DESC, s.agent_name;


ALTER TABLE public.session_stats_per_hour OWNER TO spacetraders;

--
-- TOC entry 262 (class 1259 OID 79128)
-- Name: ship_cargo; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_cargo (
    ship_symbol text NOT NULL,
    trade_symbol text NOT NULL,
    quantity numeric NOT NULL
);


ALTER TABLE public.ship_cargo OWNER TO spacetraders;

--
-- TOC entry 227 (class 1259 OID 40567)
-- Name: ship_cooldowns; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_cooldowns (
    ship_symbol text NOT NULL,
    total_seconds integer,
    expiration timestamp without time zone NOT NULL
);


ALTER TABLE public.ship_cooldowns OWNER TO spacetraders;

--
-- TOC entry 256 (class 1259 OID 77318)
-- Name: ship_cooldown; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.ship_cooldown AS
 WITH maxes AS (
         SELECT ship_cooldowns.ship_symbol,
            max(ship_cooldowns.expiration) AS expiration
           FROM public.ship_cooldowns
          GROUP BY ship_cooldowns.ship_symbol
        )
 SELECT sc.ship_symbol,
    sc.total_seconds,
    sc.expiration,
        CASE
            WHEN (sc.expiration < timezone('utc'::text, now())) THEN '00:00:00'::interval
            ELSE (sc.expiration - timezone('utc'::text, now()))
        END AS remaining,
        CASE
            WHEN (sc.expiration < timezone('utc'::text, now())) THEN false
            ELSE true
        END AS cd_active
   FROM (maxes m
     JOIN public.ship_cooldowns sc ON (((m.ship_symbol = sc.ship_symbol) AND (m.expiration = sc.expiration))));


ALTER TABLE public.ship_cooldown OWNER TO spacetraders;

--
-- TOC entry 228 (class 1259 OID 40578)
-- Name: ship_frame_links; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_frame_links (
    ship_symbol text NOT NULL,
    frame_symbol text NOT NULL,
    condition integer
);


ALTER TABLE public.ship_frame_links OWNER TO spacetraders;

--
-- TOC entry 229 (class 1259 OID 40584)
-- Name: ship_frames; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_frames (
    frame_symbol text NOT NULL,
    name text,
    description text,
    module_slots integer,
    mount_points integer,
    fuel_capacity integer,
    required_power integer,
    required_crew integer,
    required_slots integer
);


ALTER TABLE public.ship_frames OWNER TO spacetraders;

--
-- TOC entry 247 (class 1259 OID 55936)
-- Name: ship_mounts; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_mounts (
    mount_symbol text NOT NULL,
    mount_name text,
    mount_desc text,
    strength integer,
    required_crew integer,
    required_power integer
);


ALTER TABLE public.ship_mounts OWNER TO spacetraders;

--
-- TOC entry 230 (class 1259 OID 40599)
-- Name: ship_nav; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_nav (
    ship_symbol text NOT NULL,
    system_symbol text NOT NULL,
    waypoint_symbol text NOT NULL,
    departure_time timestamp without time zone NOT NULL,
    arrival_time timestamp without time zone NOT NULL,
    o_waypoint_symbol text NOT NULL,
    d_waypoint_symbol text NOT NULL,
    flight_status text NOT NULL,
    flight_mode text NOT NULL
);


ALTER TABLE public.ship_nav OWNER TO spacetraders;

--
-- TOC entry 255 (class 1259 OID 77314)
-- Name: ship_nav_time; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.ship_nav_time AS
 WITH nav_time AS (
         SELECT ship_nav.ship_symbol,
            (ship_nav.arrival_time - timezone('utc'::text, now())) AS timetoarrive
           FROM public.ship_nav
        )
 SELECT nt.ship_symbol,
        CASE
            WHEN (nt.timetoarrive < '00:00:00'::interval) THEN '00:00:00'::interval
            ELSE nt.timetoarrive
        END AS remaining_time,
        CASE
            WHEN (nt.timetoarrive < '00:00:00'::interval) THEN false
            ELSE true
        END AS flight_active
   FROM nav_time nt;


ALTER TABLE public.ship_nav_time OWNER TO spacetraders;

--
-- TOC entry 257 (class 1259 OID 77323)
-- Name: ship_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.ship_overview AS
 SELECT s.agent_name,
    s.ship_symbol,
    s.ship_role,
    sfl.frame_symbol,
    sn.waypoint_symbol,
    s.cargo_in_use,
    s.cargo_capacity,
    sb.behaviour_id,
    sb.behaviour_params,
    sb.locked_until,
    (sc.cd_active OR (sn.arrival_time >= timezone('utc'::text, now()))) AS cooldown_nav,
    date_trunc('SECONDS'::text, s.last_updated) AS last_updated
   FROM ((((public.ships s
     LEFT JOIN public.ship_behaviours sb ON ((s.ship_symbol = sb.ship_symbol)))
     JOIN public.ship_frame_links sfl ON ((s.ship_symbol = sfl.ship_symbol)))
     JOIN public.ship_nav sn ON ((s.ship_symbol = sn.ship_symbol)))
     LEFT JOIN public.ship_cooldown sc ON ((s.ship_symbol = sc.ship_symbol)))
  ORDER BY s.agent_name, s.ship_role, sfl.frame_symbol, s.last_updated DESC;


ALTER TABLE public.ship_overview OWNER TO spacetraders;

--
-- TOC entry 243 (class 1259 OID 52482)
-- Name: ship_performance; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.ship_performance AS
 SELECT mat_session_stats.ship_symbol,
    date_trunc('hour'::text, mat_session_stats.session_start) AS hour,
    mat_session_stats.behaviour_id,
    sum(mat_session_stats.earnings) AS cph,
    sum(mat_session_stats.requests) AS requests,
    COALESCE((sum(mat_session_stats.earnings) / NULLIF(sum(mat_session_stats.requests), (0)::numeric)), (0)::numeric) AS cpr
   FROM public.mat_session_stats
  WHERE (mat_session_stats.session_start >= (date_trunc('hour'::text, now()) - '06:00:00'::interval))
  GROUP BY mat_session_stats.ship_symbol, (date_trunc('hour'::text, mat_session_stats.session_start)), mat_session_stats.behaviour_id
  ORDER BY mat_session_stats.ship_symbol, (date_trunc('hour'::text, mat_session_stats.session_start)), mat_session_stats.behaviour_id;


ALTER TABLE public.ship_performance OWNER TO spacetraders;

--
-- TOC entry 245 (class 1259 OID 52685)
-- Name: ship_tasks; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.ship_tasks (
    task_hash text NOT NULL,
    agent_symbol text,
    requirements text[],
    expiry timestamp without time zone,
    priority numeric,
    claimed_by text,
    behaviour_id text,
    target_system text,
    behaviour_params jsonb,
    completed boolean
);


ALTER TABLE public.ship_tasks OWNER TO spacetraders;

--
-- TOC entry 231 (class 1259 OID 40610)
-- Name: shipyard_prices; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.shipyard_prices AS
 WITH ranked_shipyard AS (
         SELECT shipyard_types.ship_type,
            shipyard_types.ship_cost,
            shipyard_types.shipyard_symbol,
            row_number() OVER (PARTITION BY shipyard_types.ship_type ORDER BY shipyard_types.ship_cost, shipyard_types.shipyard_symbol) AS rank
           FROM public.shipyard_types
        )
 SELECT st.ship_type,
    min(st.ship_cost) AS best_price,
    count(
        CASE
            WHEN (st.ship_cost IS NOT NULL) THEN 1
            ELSE NULL::integer
        END) AS sources,
    count(*) AS locations,
    rs.shipyard_symbol AS cheapest_location
   FROM (public.shipyard_types st
     LEFT JOIN ranked_shipyard rs ON ((st.ship_type = rs.ship_type)))
  WHERE (rs.rank = 1)
  GROUP BY st.ship_type, rs.shipyard_symbol
  ORDER BY st.ship_type;


ALTER TABLE public.shipyard_prices OWNER TO spacetraders;

--
-- TOC entry 241 (class 1259 OID 41005)
-- Name: shipyard_type_performance; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.shipyard_type_performance AS
 WITH data AS (
         SELECT s_1.agent_name,
            mss_1.ship_symbol,
            date_trunc('hour'::text, mss_1.session_start) AS date_trunc,
            sum(mss_1.earnings) AS earnings,
            sum(mss_1.requests) AS requests,
            count(*) AS sessions
           FROM (public.mat_session_stats mss_1
             JOIN public.ships s_1 ON ((mss_1.ship_symbol = s_1.ship_symbol)))
          WHERE (mss_1.session_start >= (timezone('utc'::text, now()) - '06:00:00'::interval))
          GROUP BY s_1.agent_name, mss_1.ship_symbol, (date_trunc('hour'::text, mss_1.session_start))
        )
 SELECT s.agent_name,
    COALESCE(msts.shipyard_type, (s.ship_role || sf.frame_symbol)) AS shipyard_type,
    sp.best_price,
    count(DISTINCT s.ship_symbol) AS count_of_ships,
    sum(mss.earnings) AS earnings,
    sum(mss.requests) AS requests,
    sum(mss.sessions) AS sessions,
    (sum(mss.earnings) / (count(*))::numeric) AS cph,
    (sum(mss.earnings) / sum(mss.requests)) AS cpr
   FROM ((((data mss
     JOIN public.ships s ON ((mss.ship_symbol = s.ship_symbol)))
     JOIN public.ship_frame_links sf ON ((s.ship_symbol = sf.ship_symbol)))
     LEFT JOIN public.mat_shipyardtypes_to_ship msts ON (((s.ship_role || sf.frame_symbol) = msts.ship_roleframe)))
     LEFT JOIN public.shipyard_prices sp ON ((sp.ship_type = msts.shipyard_type)))
  GROUP BY s.agent_name, COALESCE(msts.shipyard_type, (s.ship_role || sf.frame_symbol)), sp.best_price
  ORDER BY (sum(mss.earnings) / (count(*))::numeric) DESC;


ALTER TABLE public.shipyard_type_performance OWNER TO spacetraders;

--
-- TOC entry 269 (class 1259 OID 79851)
-- Name: survey_average_values; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.survey_average_values AS
SELECT
    NULL::text AS signature,
    NULL::text AS waypoint_symbol,
    NULL::timestamp without time zone AS expiration,
    NULL::text AS size,
    NULL::numeric AS survey_value;


ALTER TABLE public.survey_average_values OWNER TO spacetraders;

--
-- TOC entry 232 (class 1259 OID 40624)
-- Name: survey_deposits; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.survey_deposits (
    signature text NOT NULL,
    trade_symbol text NOT NULL,
    count integer
);


ALTER TABLE public.survey_deposits OWNER TO spacetraders;

--
-- TOC entry 233 (class 1259 OID 40630)
-- Name: surveys; Type: TABLE; Schema: public; Owner: spacetraders
--

CREATE TABLE public.surveys (
    signature text NOT NULL,
    waypoint_symbol text,
    expiration timestamp without time zone,
    size text,
    exhausted boolean DEFAULT false
);


ALTER TABLE public.surveys OWNER TO spacetraders;

--
-- TOC entry 270 (class 1259 OID 79856)
-- Name: survey_chance_and_values; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.survey_chance_and_values AS
 WITH totals AS (
         SELECT sd_1.signature,
            count(*) AS total_deposits
           FROM public.survey_deposits sd_1
          GROUP BY sd_1.signature
        )
 SELECT sd.signature,
    sd.trade_symbol,
    sd.count,
    tot.total_deposits,
    round(((sd.count)::numeric / (tot.total_deposits)::numeric), 2) AS chance,
    sav.survey_value
   FROM (((public.survey_deposits sd
     JOIN public.surveys s ON ((s.signature = sd.signature)))
     JOIN totals tot ON ((sd.signature = tot.signature)))
     JOIN public.survey_average_values sav ON ((sd.signature = sav.signature)))
  WHERE ((s.expiration >= timezone('utc'::text, now())) AND (s.exhausted = false))
  ORDER BY (round(((sd.count)::numeric / (tot.total_deposits)::numeric), 2)) DESC, sav.survey_value DESC;


ALTER TABLE public.survey_chance_and_values OWNER TO spacetraders;

--
-- TOC entry 253 (class 1259 OID 66196)
-- Name: survey_throughput; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.survey_throughput AS
 SELECT date_trunc('hour'::text, logging.event_timestamp) AS date_trunc,
    count(*) FILTER (WHERE (logging.event_name = 'ship_survey'::text)) AS new_surveys,
    count(DISTINCT (logging.event_params ->> 'survey_id'::text)) FILTER (WHERE (logging.event_name = 'survey_exhausted'::text)) AS exhausted_surveys
   FROM public.logging
  WHERE ((logging.event_name = ANY (ARRAY['ship_survey'::text, 'survey_exhausted'::text])) AND (logging.event_timestamp >= (now() - '1 day'::interval)))
  GROUP BY (date_trunc('hour'::text, logging.event_timestamp))
  ORDER BY (date_trunc('hour'::text, logging.event_timestamp)) DESC, (count(*) FILTER (WHERE (logging.event_name = 'ship_survey'::text)));


ALTER TABLE public.survey_throughput OWNER TO spacetraders;

--
-- TOC entry 238 (class 1259 OID 40836)
-- Name: systems_on_network_but_uncharted; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.systems_on_network_but_uncharted AS
 SELECT jc.d_system_symbol AS system_symbol
   FROM ((public.jumpgate_connections jc
     LEFT JOIN public.systems s ON ((jc.d_system_symbol = s.system_symbol)))
     LEFT JOIN public.waypoints w2 ON ((w2.system_symbol = s.system_symbol)))
  WHERE ((((w2.type = 'JUMP_GATE'::text) OR (w2.type IS NULL)) AND (w2.checked IS FALSE)) OR (w2.checked IS NULL));


ALTER TABLE public.systems_on_network_but_uncharted OWNER TO spacetraders;

--
-- TOC entry 254 (class 1259 OID 67586)
-- Name: systems_with_jumpgates; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.systems_with_jumpgates AS
 SELECT DISTINCT w.system_symbol
   FROM (public.jump_gates jg
     JOIN public.waypoints w ON ((jg.waypoint_symbol = w.waypoint_symbol)));


ALTER TABLE public.systems_with_jumpgates OWNER TO spacetraders;

--
-- TOC entry 264 (class 1259 OID 79358)
-- Name: task_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.task_overview AS
 SELECT ship_tasks.expiry,
        CASE
            WHEN (ship_tasks.completed = true) THEN NULL::numeric
            ELSE ship_tasks.priority
        END AS pending_priority,
    COALESCE(ship_tasks.claimed_by, ship_tasks.agent_symbol) AS assignee,
    ship_tasks.behaviour_id,
    ship_tasks.behaviour_params
   FROM public.ship_tasks
  WHERE ((ship_tasks.claimed_by IS NOT NULL) OR (ship_tasks.expiry > now()))
  ORDER BY (ship_tasks.expiry IS NULL), ship_tasks.expiry DESC,
        CASE
            WHEN (ship_tasks.completed = true) THEN NULL::numeric
            ELSE ship_tasks.priority
        END;


ALTER TABLE public.task_overview OWNER TO spacetraders;

--
-- TOC entry 263 (class 1259 OID 79149)
-- Name: trade_extraction_packages; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.trade_extraction_packages AS
 WITH cargo_packages AS (
         SELECT w.system_symbol,
            w.waypoint_symbol AS source_waypoint,
            w.x AS origin_x,
            w.y AS origin_y,
            sc.trade_symbol,
            sum(sc.quantity) AS quantity
           FROM (((public.ship_cargo sc
             JOIN public.ships s ON ((sc.ship_symbol = s.ship_symbol)))
             JOIN public.ship_nav sn ON ((sn.ship_symbol = s.ship_symbol)))
             JOIN public.waypoints w ON ((sn.waypoint_symbol = w.waypoint_symbol)))
          WHERE (s.ship_role = 'EXCAVATOR'::text)
          GROUP BY w.system_symbol, w.waypoint_symbol, w.x, w.y, sc.trade_symbol
          ORDER BY w.waypoint_symbol
        ), package_values AS (
         SELECT cp.source_waypoint,
            cp.trade_symbol,
            mtl.market_symbol,
            ((mtl.sell_price)::numeric * cp.quantity) AS line_item_value,
            cp.quantity,
            sqrt(((((cp.origin_x - w.x))::double precision ^ (2)::double precision) + (((cp.origin_y - w.y))::double precision ^ (2)::double precision))) AS distance
           FROM ((cargo_packages cp
             JOIN public.market_tradegood_listings mtl ON ((cp.trade_symbol = mtl.trade_symbol)))
             JOIN public.waypoints w ON ((w.waypoint_symbol = mtl.market_symbol)))
        ), compiled_data AS (
         SELECT package_values.source_waypoint,
            package_values.market_symbol,
            sum(package_values.line_item_value) AS package_value,
            sum(package_values.quantity) AS package_size,
            array_agg(package_values.trade_symbol) AS trade_symbols,
            package_values.distance
           FROM package_values
          GROUP BY package_values.source_waypoint, package_values.market_symbol, package_values.distance
          ORDER BY package_values.source_waypoint, (sum(package_values.line_item_value)) DESC
        )
 SELECT compiled_data.source_waypoint,
    compiled_data.market_symbol,
    compiled_data.trade_symbols,
    compiled_data.package_value,
    compiled_data.package_size,
    compiled_data.distance
   FROM compiled_data
  ORDER BY compiled_data.package_size DESC, compiled_data.source_waypoint, ((compiled_data.package_value)::double precision / GREATEST(compiled_data.distance, (1)::double precision)) DESC;


ALTER TABLE public.trade_extraction_packages OWNER TO spacetraders;

--
-- TOC entry 261 (class 1259 OID 79019)
-- Name: trade_routes_extraction_intrasystem; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.trade_routes_extraction_intrasystem AS
 WITH traits_and_tradegoods(trait_symbol, trade_symbol) AS (
         VALUES ('COMMON_METAL_DEPOSITS'::text,'IRON_ORE'::text), ('COMMON_METAL_DEPOSITS'::text,'COPPER_ORE'::text), ('COMMON_METAL_DEPOSITS'::text,'ALUMINUM_ORE'::text), ('EXPLOSIVE_GASES'::text,'HYDROCARBON'::text), ('ICE_CRYSTALS'::text,'AMMONIA_ICE'::text), ('ICE_CRYSTALS'::text,'LIQUID_HYDROGEN'::text), ('ICE_CRYSTALS'::text,'LIQUID_NITROGEN'::text), ('ICE_CRYSTALS'::text,'ICE_WATER'::text), ('MINERAL_DEPOSITS'::text,'SILICON_CRYSTALS'::text), ('MINERAL_DEPOSITS'::text,'QUARTZ_SAND'::text), ('PRECIOUS_METAL_DEPOSITS'::text,'GOLD_ORE'::text), ('PRECIOUS_METAL_DEPOSITS'::text,'SILVER_ORE'::text), ('PRECIOUS_METAL_DEPOSITS'::text,'PLATINUM_ORE'::text), ('RARE_METAL_DEPOSITS'::text,'URANITE_ORE'::text), ('RARE_METAL_DEPOSITS'::text,'MERITIUM_ORE'::text)
        ), routes AS (
         SELECT w1.system_symbol,
            tat.trade_symbol,
            mtl.sell_price AS profit_per_unit,
            w2.waypoint_symbol AS extraction_waypoint,
            w2.x AS extract_x,
            w2.y AS extract_y,
            mtl.supply AS import_supply,
            mtl.market_depth,
            mtl.market_symbol AS import_market,
            w1.x AS import_x,
            w1.y AS import_y,
            sqrt(((((w1.x - w2.x))::double precision ^ (2)::double precision) + (((w1.y - w2.y))::double precision ^ (2)::double precision))) AS distance
           FROM ((((public.market_tradegood_listings mtl
             JOIN traits_and_tradegoods tat ON ((mtl.trade_symbol = tat.trade_symbol)))
             JOIN public.waypoints w1 ON ((mtl.market_symbol = w1.waypoint_symbol)))
             JOIN public.waypoint_traits wt ON ((tat.trait_symbol = wt.trait_symbol)))
             JOIN public.waypoints w2 ON (((wt.waypoint_symbol = w2.waypoint_symbol) AND (w2.system_symbol = w1.system_symbol))))
          WHERE ((mtl.type = 'IMPORT'::text) AND (w2.type = ANY (ARRAY['ASTEROID'::text, 'ENGINEERED_ASTEROID'::text, 'ASTEROID_BASE'::text])))
        ), final_results AS (
         SELECT ((((routes.profit_per_unit * LEAST(routes.market_depth, 100)) * 5))::double precision / (routes.distance + (15)::double precision)) AS route_value,
            routes.system_symbol,
            routes.trade_symbol,
            routes.profit_per_unit,
            routes.extraction_waypoint,
            routes.extract_x,
            routes.extract_y,
            0 AS buy_price,
            routes.profit_per_unit AS sell_price,
            'INFINITE'::text AS export_supply,
            routes.import_supply,
            routes.market_depth,
            routes.import_market,
            routes.import_x,
            routes.import_y,
            routes.distance
           FROM routes
          WHERE ((routes.profit_per_unit > 0) AND (routes.extraction_waypoint <> routes.import_market))
          ORDER BY ((((routes.profit_per_unit * routes.market_depth) * 5))::double precision / (routes.distance + (15)::double precision)) DESC
        )
 SELECT final_results.route_value,
    final_results.system_symbol,
    final_results.trade_symbol,
    final_results.profit_per_unit,
    final_results.extraction_waypoint,
    final_results.extract_x,
    final_results.extract_y,
    final_results.buy_price,
    final_results.sell_price,
    final_results.export_supply,
    final_results.import_supply,
    final_results.market_depth,
    final_results.import_market,
    final_results.import_x,
    final_results.import_y,
    final_results.distance
   FROM final_results
  ORDER BY final_results.route_value DESC;


ALTER TABLE public.trade_routes_extraction_intrasystem OWNER TO spacetraders;

--
-- TOC entry 259 (class 1259 OID 78121)
-- Name: trade_routes_intrasystem; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.trade_routes_intrasystem AS
 WITH exports AS (
         SELECT mtl.market_symbol,
            w.x,
            w.y,
            mtl.trade_symbol,
            mtl.purchase_price,
            mtl.supply,
            mtl.market_depth,
            mtl.activity,
            w.system_symbol
           FROM (public.market_tradegood_listings mtl
             JOIN public.waypoints w ON ((mtl.market_symbol = w.waypoint_symbol)))
          WHERE (mtl.type = ANY (ARRAY['EXPORT'::text]))
          ORDER BY mtl.market_depth DESC, mtl.supply
        ), imports AS (
         SELECT mtl.market_symbol,
            w.x,
            w.y,
            mtl.trade_symbol,
            mtl.sell_price,
            mtl.supply,
            mtl.market_depth,
            mtl.activity,
            w.system_symbol
           FROM (public.market_tradegood_listings mtl
             JOIN public.waypoints w ON ((mtl.market_symbol = w.waypoint_symbol)))
          WHERE (mtl.type = ANY (ARRAY['IMPORT'::text, 'EXCHANGE'::text]))
          ORDER BY mtl.market_depth DESC, mtl.supply
        ), routes AS (
         SELECT e.system_symbol,
            e.trade_symbol,
            (i.sell_price - e.purchase_price) AS profit_per_unit,
            e.market_symbol AS export_market,
            e.x AS export_x,
            e.y AS export_y,
            e.purchase_price,
            i.sell_price,
                CASE
                    WHEN (e.supply = 'ABUNDANT'::text) THEN 5
                    ELSE
                    CASE
                        WHEN (e.supply = 'HIGH'::text) THEN 4
                        ELSE
                        CASE
                            WHEN (e.supply = 'MODERATE'::text) THEN 3
                            ELSE
                            CASE
                                WHEN (e.supply = 'LIMITED'::text) THEN 2
                                ELSE
                                CASE
                                    WHEN (e.supply = 'SCARCE'::text) THEN 1
                                    ELSE 1
                                END
                            END
                        END
                    END
                END AS supply_value,
            e.supply AS supply_text,
                CASE
                    WHEN (i.supply = 'ABUNDANT'::text) THEN 1
                    ELSE
                    CASE
                        WHEN (i.supply = 'HIGH'::text) THEN 2
                        ELSE
                        CASE
                            WHEN (i.supply = 'MODERATE'::text) THEN 3
                            ELSE
                            CASE
                                WHEN (i.supply = 'LIMITED'::text) THEN 4
                                ELSE
                                CASE
                                    WHEN (i.supply = 'SCARCE'::text) THEN 5
                                    ELSE 1
                                END
                            END
                        END
                    END
                END AS import_supply_value,
            i.supply AS import_supply,
            LEAST(e.market_depth, i.market_depth) AS market_depth,
            i.market_symbol AS import_market,
            i.x AS import_x,
            i.y AS import_y,
            sqrt(((((e.x - i.x))::double precision ^ (2)::double precision) + (((e.y - i.y))::double precision ^ (2)::double precision))) AS distance
           FROM (exports e
             JOIN imports i ON (((e.trade_symbol = i.trade_symbol) AND (e.system_symbol = i.system_symbol) AND (e.market_symbol <> i.market_symbol))))
        )
 SELECT ((((routes.profit_per_unit * LEAST(routes.market_depth, 100)) * routes.supply_value))::double precision / (routes.distance + (15)::double precision)) AS route_value,
    routes.system_symbol,
    routes.trade_symbol,
    routes.profit_per_unit,
    routes.export_market,
    routes.export_x,
    routes.export_y,
    routes.purchase_price,
    routes.sell_price,
    routes.supply_value,
    routes.supply_text,
    routes.import_supply,
    routes.market_depth,
    routes.import_market,
    routes.import_x,
    routes.import_y,
    routes.distance
   FROM routes
  WHERE ((routes.profit_per_unit > 0) AND (((routes.sell_price)::double precision / (routes.purchase_price)::double precision) > (
        CASE
            WHEN (routes.market_depth = 10) THEN 1.15
            ELSE (1)::numeric
        END)::double precision))
  ORDER BY ((((routes.profit_per_unit * routes.market_depth) * routes.supply_value))::double precision / (routes.distance + (15)::double precision)) DESC;


ALTER TABLE public.trade_routes_intrasystem OWNER TO spacetraders;

--
-- TOC entry 271 (class 1259 OID 84831)
-- Name: trade_routes_max_potentials; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.trade_routes_max_potentials AS
 WITH extremes AS (
         SELECT mc.trade_symbol,
            max(
                CASE
                    WHEN (mc.type = 'IMPORT'::text) THEN mc.current_sell_price
                    ELSE NULL::numeric
                END) AS max_import_price,
            min(
                CASE
                    WHEN (mc.type = 'EXPORT'::text) THEN mc.current_purchase_price
                    ELSE NULL::numeric
                END) AS min_export_price
           FROM public.market_changes mc
          WHERE (mc.type <> 'EXCHANGE'::text)
          GROUP BY mc.trade_symbol
        )
 SELECT extremes.trade_symbol,
    extremes.max_import_price,
    extremes.min_export_price,
    round(((extremes.max_import_price / extremes.min_export_price) * (100)::numeric), 2) AS profit_pct
   FROM extremes;


ALTER TABLE public.trade_routes_max_potentials OWNER TO spacetraders;

--
-- TOC entry 274 (class 1259 OID 93042)
-- Name: transaction_overview; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.transaction_overview AS
 SELECT min(t."timestamp") AS first_transaction_in_session,
    t.ship_symbol,
    t.trade_symbol,
    sum(t.units) AS units,
    round(avg(
        CASE
            WHEN (t.type = 'SELL'::text) THEN t.price_per_unit
            ELSE NULL::integer
        END)) AS average_sell_price,
    round(avg(
        CASE
            WHEN (t.type = 'PURCHASE'::text) THEN t.price_per_unit
            ELSE NULL::integer
        END)) AS average_purchase_price,
    sum((t.total_price * (
        CASE
            WHEN (t.type = 'PURCHASE'::text) THEN '-1'::integer
            ELSE 1
        END)::numeric)) AS net_change,
    string_agg(DISTINCT
        CASE
            WHEN (t.type = 'PURCHASE'::text) THEN t.waypoint_symbol
            ELSE NULL::text
        END, ''::text) AS purchase_wp,
    string_agg(DISTINCT
        CASE
            WHEN (t.type = 'SELL'::text) THEN t.waypoint_symbol
            ELSE NULL::text
        END, ','::text) AS sell_wp,
    t.session_id
   FROM (public.transactions t
     JOIN public.ships s ON ((t.ship_symbol = s.ship_symbol)))
  WHERE (s.ship_role <> 'EXCAVATOR'::text)
  GROUP BY t.ship_symbol, t.trade_symbol, t.session_id
 HAVING (min(t."timestamp") >= (timezone('utc'::text, now()) - '06:00:00'::interval))
  ORDER BY (min(t."timestamp")) DESC;


ALTER TABLE public.transaction_overview OWNER TO spacetraders;

--
-- TOC entry 234 (class 1259 OID 40641)
-- Name: waypoint_types_not_scanned_by_system; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.waypoint_types_not_scanned_by_system AS
 SELECT w.type,
    w.system_symbol
   FROM (public.waypoints w
     LEFT JOIN public.waypoint_traits wt ON ((w.waypoint_symbol = wt.waypoint_symbol)))
  GROUP BY w.type, w.system_symbol
 HAVING (count(wt.trait_symbol) = 0);


ALTER TABLE public.waypoint_types_not_scanned_by_system OWNER TO spacetraders;

--
-- TOC entry 235 (class 1259 OID 40645)
-- Name: waypoints_not_scanned; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.waypoints_not_scanned AS
 SELECT w.waypoint_symbol,
    w.type,
    w.system_symbol,
    w.x,
    w.y
   FROM public.waypoints w
  WHERE (NOT w.checked);


ALTER TABLE public.waypoints_not_scanned OWNER TO spacetraders;

--
-- TOC entry 236 (class 1259 OID 40649)
-- Name: waypoints_not_scanned_progress; Type: VIEW; Schema: public; Owner: spacetraders
--

CREATE VIEW public.waypoints_not_scanned_progress AS
 WITH waypoint_scan_progress AS (
         SELECT count(
                CASE
                    WHEN (NOT w.checked) THEN 1
                    ELSE NULL::integer
                END) AS remaining,
            count(*) AS total
           FROM public.waypoints w
          WHERE (w.type = ANY (ARRAY['ORBITAL_STATION'::text, 'ASTEROID_FIELD'::text, 'JUMP_GATE'::text]))
        )
 SELECT 'Waypoint scanning progress'::text AS "?column?",
    (waypoint_scan_progress.total - waypoint_scan_progress.remaining) AS scanned,
    waypoint_scan_progress.total,
    round(((((waypoint_scan_progress.total - waypoint_scan_progress.remaining))::numeric / (waypoint_scan_progress.total)::numeric) * (100)::numeric), 2) AS progress
   FROM waypoint_scan_progress;


ALTER TABLE public.waypoints_not_scanned_progress OWNER TO spacetraders;

--
-- TOC entry 3182 (class 2606 OID 40655)
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (agent_symbol);


--
-- TOC entry 3192 (class 2606 OID 40657)
-- Name: contract_tradegoods contract_tradegoods_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.contract_tradegoods
    ADD CONSTRAINT contract_tradegoods_pkey PRIMARY KEY (contract_id, trade_symbol);


--
-- TOC entry 3194 (class 2606 OID 40659)
-- Name: contracts contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_pkey PRIMARY KEY (id);


--
-- TOC entry 3232 (class 2606 OID 64907)
-- Name: extractions extractions_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.extractions
    ADD CONSTRAINT extractions_pkey PRIMARY KEY (ship_symbol, event_timestamp);


--
-- TOC entry 3196 (class 2606 OID 40661)
-- Name: jump_gates jump_gates_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.jump_gates
    ADD CONSTRAINT jump_gates_pkey PRIMARY KEY (waypoint_symbol);


--
-- TOC entry 3226 (class 2606 OID 40835)
-- Name: jumpgate_connections jumpgate_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.jumpgate_connections
    ADD CONSTRAINT jumpgate_connections_pkey PRIMARY KEY (s_system_symbol, d_system_symbol);


--
-- TOC entry 3188 (class 2606 OID 40665)
-- Name: logging logging_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.logging
    ADD CONSTRAINT logging_pkey PRIMARY KEY (event_timestamp, ship_symbol);


--
-- TOC entry 3236 (class 2606 OID 79523)
-- Name: manufacture_relationships manufacture_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.manufacture_relationships
    ADD CONSTRAINT manufacture_relationships_pkey PRIMARY KEY (export_tradegood, import_tradegoods);


--
-- TOC entry 3204 (class 2606 OID 40667)
-- Name: market market_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.market
    ADD CONSTRAINT market_pkey PRIMARY KEY (symbol);


--
-- TOC entry 3208 (class 2606 OID 40669)
-- Name: market_tradegood market_tradegood_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.market_tradegood
    ADD CONSTRAINT market_tradegood_pkey PRIMARY KEY (market_waypoint, symbol);


--
-- TOC entry 3190 (class 2606 OID 40671)
-- Name: ship_behaviours ship_behaviours_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_behaviours
    ADD CONSTRAINT ship_behaviours_pkey PRIMARY KEY (ship_symbol);


--
-- TOC entry 3214 (class 2606 OID 40673)
-- Name: ship_cooldowns ship_cooldown_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_cooldowns
    ADD CONSTRAINT ship_cooldown_pkey PRIMARY KEY (ship_symbol, expiration);


--
-- TOC entry 3216 (class 2606 OID 40675)
-- Name: ship_frame_links ship_frame_links_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_frame_links
    ADD CONSTRAINT ship_frame_links_pkey PRIMARY KEY (ship_symbol, frame_symbol);


--
-- TOC entry 3218 (class 2606 OID 40677)
-- Name: ship_frames ship_frames_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_frames
    ADD CONSTRAINT ship_frames_pkey PRIMARY KEY (frame_symbol);


--
-- TOC entry 3234 (class 2606 OID 79135)
-- Name: ship_cargo ship_inventories_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_cargo
    ADD CONSTRAINT ship_inventories_pkey PRIMARY KEY (ship_symbol, trade_symbol);


--
-- TOC entry 3230 (class 2606 OID 55943)
-- Name: ship_mounts ship_mounts_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_mounts
    ADD CONSTRAINT ship_mounts_pkey PRIMARY KEY (mount_symbol);


--
-- TOC entry 3220 (class 2606 OID 40681)
-- Name: ship_nav ship_nav_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_nav
    ADD CONSTRAINT ship_nav_pkey PRIMARY KEY (ship_symbol);


--
-- TOC entry 3184 (class 2606 OID 40683)
-- Name: ships ship_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ships
    ADD CONSTRAINT ship_pkey PRIMARY KEY (ship_symbol);


--
-- TOC entry 3228 (class 2606 OID 52692)
-- Name: ship_tasks ship_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.ship_tasks
    ADD CONSTRAINT ship_tasks_pkey PRIMARY KEY (task_hash);


--
-- TOC entry 3210 (class 2606 OID 40685)
-- Name: shipyard_types shipyard_types_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.shipyard_types
    ADD CONSTRAINT shipyard_types_pkey PRIMARY KEY (shipyard_symbol, ship_type);


--
-- TOC entry 3222 (class 2606 OID 40687)
-- Name: survey_deposits survey_deposit_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.survey_deposits
    ADD CONSTRAINT survey_deposit_pkey PRIMARY KEY (signature, trade_symbol);


--
-- TOC entry 3224 (class 2606 OID 40689)
-- Name: surveys survey_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT survey_pkey PRIMARY KEY (signature);


--
-- TOC entry 3212 (class 2606 OID 40691)
-- Name: systems systems_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.systems
    ADD CONSTRAINT systems_pkey PRIMARY KEY (system_symbol);


--
-- TOC entry 3206 (class 2606 OID 40693)
-- Name: market_tradegood_listings tradegoods_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.market_tradegood_listings
    ADD CONSTRAINT tradegoods_pkey PRIMARY KEY (market_symbol, trade_symbol);


--
-- TOC entry 3186 (class 2606 OID 40695)
-- Name: transactions transaction_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transaction_pkey PRIMARY KEY ("timestamp", ship_symbol);


--
-- TOC entry 3198 (class 2606 OID 40697)
-- Name: waypoint_charts waypoint_charts_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.waypoint_charts
    ADD CONSTRAINT waypoint_charts_pkey PRIMARY KEY (waypoint_symbol);


--
-- TOC entry 3202 (class 2606 OID 40699)
-- Name: waypoints waypoint_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.waypoints
    ADD CONSTRAINT waypoint_pkey PRIMARY KEY (waypoint_symbol);


--
-- TOC entry 3200 (class 2606 OID 40701)
-- Name: waypoint_traits waypoint_traits_pkey; Type: CONSTRAINT; Schema: public; Owner: spacetraders
--

ALTER TABLE ONLY public.waypoint_traits
    ADD CONSTRAINT waypoint_traits_pkey PRIMARY KEY (waypoint_symbol, trait_symbol);


--
-- TOC entry 3407 (class 2618 OID 79854)
-- Name: survey_average_values _RETURN; Type: RULE; Schema: public; Owner: spacetraders
--

CREATE OR REPLACE VIEW public.survey_average_values AS
 SELECT s.signature,
    s.waypoint_symbol,
    s.expiration,
    s.size,
    round((sum((mp.import_price * (sd.count)::numeric)) / (sum(sd.count))::numeric), 2) AS survey_value
   FROM ((public.surveys s
     JOIN public.survey_deposits sd ON ((s.signature = sd.signature)))
     JOIN public.market_prices mp ON ((mp.trade_symbol = sd.trade_symbol)))
  WHERE (s.expiration >= timezone('utc'::text, now()))
  GROUP BY s.signature, s.waypoint_symbol, s.expiration
  ORDER BY (sum((mp.import_price * (sd.count)::numeric)) / (sum(sd.count))::numeric) DESC, s.expiration;


--
-- TOC entry 3411 (class 2618 OID 84866)
-- Name: export_overview _RETURN; Type: RULE; Schema: public; Owner: spacetraders
--

CREATE OR REPLACE VIEW public.export_overview AS
 SELECT w.system_symbol,
    mtl.market_symbol,
    mtl.trade_symbol,
    mtl.supply,
    mtl.activity,
    mtl.purchase_price,
    mtl.sell_price,
    mtl.market_depth,
    sum(
        CASE
            WHEN (t."timestamp" > (now() - '01:00:00'::interval)) THEN t.units
            ELSE NULL::integer
        END) AS units_sold_recently,
    mr.import_tradegoods AS requirements
   FROM (((public.market_tradegood_listings mtl
     JOIN public.waypoints w ON ((w.waypoint_symbol = mtl.market_symbol)))
     LEFT JOIN public.transactions t ON (((t.waypoint_symbol = w.waypoint_symbol) AND (t.trade_symbol = mtl.trade_symbol))))
     LEFT JOIN public.manufacture_relationships mr ON ((mr.export_tradegood = mtl.trade_symbol)))
  WHERE (mtl.type = 'EXPORT'::text)
  GROUP BY w.system_symbol, mtl.market_symbol, mtl.trade_symbol, mr.import_tradegoods
  ORDER BY w.system_symbol, (mtl.activity <> 'RESTRICTED'::text), mtl.trade_symbol;


--
-- TOC entry 3418 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: spacetraders
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2023-12-11 15:54:21

--
-- PostgreSQL database dump complete
--

