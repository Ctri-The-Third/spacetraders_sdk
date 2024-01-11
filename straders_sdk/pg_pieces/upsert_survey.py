from ..models import Survey

import logging
import datetime
from ..utils import try_execute_upsert


def _upsert_survey(survey: Survey):
    sql = """insert into surveys (signature, waypoint_symbol, expiration, size)
    values (%s, %s, %s, %s) on conflict (signature) do nothing"""

    resp = try_execute_upsert(
        sql, (survey.signature, survey.symbol, survey.expiration, survey.size)
    )

    sql = """insert into survey_deposits (signature, trade_symbol, count) values (%s, %s, %s) on conflict (signature, trade_symbol) do nothing"""
    deposits = survey.deposits
    deposits: list
    for deposit in survey.deposits:
        count = deposits.count(deposit)
        resp = try_execute_upsert(sql, (survey.signature, deposit.symbol, count))
