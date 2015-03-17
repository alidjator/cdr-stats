#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.db import connection


def condition_switch_id(switch_id):
    """
    build where condition switch_id
    """
    try:
        int_switch = int(switch_id)
        if int_switch > 0:
            return " AND switch_id=%d " % (int_switch)
        else:
            return ""
    except ValueError:
        return ""

sqlquery_aggr_cdr_hour = """
SELECT
    dateday,
    coalesce(nbcalls,0) AS nbcalls,
    coalesce(duration,0) AS duration,
    coalesce(billsec,0) AS billsec,
    coalesce(buy_cost,0) AS buy_cost,
    coalesce(sell_cost,0) AS sell_cost
FROM
    generate_series(
                    date_trunc('hour', current_timestamp - interval '24' hour),
                    date_trunc('hour', current_timestamp),
                    '1 hour')
    AS dateday
LEFT OUTER JOIN (
    SELECT
        date_trunc('hour', starting_date) AS dayhour,
        SUM(nbcalls) AS nbcalls,
        SUM(duration) AS duration,
        SUM(billsec) AS billsec,
        SUM(buy_cost) AS buy_cost,
        SUM(sell_cost) AS sell_cost
    FROM matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('hour', current_timestamp - interval '24' hour) AND
        starting_date <= date_trunc('hour', current_timestamp)
        %(switch)s
    GROUP BY dayhour
    ) results
ON (dateday = results.dayhour);
"""


def custom_sql_matv_voip_cdr_aggr_hour(switch_id):
    """
    perform query to retrieve last 24 hours of aggregate calls data
    """
    result_hour_aggr = {}
    total_calls = total_duration = total_billsec = total_buy_cost = total_sell_cost = 0
    with connection.cursor() as cursor:
        params = {'switch': condition_switch_id(switch_id)}
        sqlquery = sqlquery_aggr_cdr_hour % params
        cursor.execute(sqlquery)
        rows = cursor.fetchall()
        i = 0
        for row in rows:
            total_calls += row[1]
            total_duration += row[2]
            total_billsec += row[3]
            total_buy_cost += row[4]
            total_sell_cost += row[5]
            result_hour_aggr[i] = {
                "calltime": row[0],
                "nbcalls": row[1],
                "duration": row[2],
                "billsec": row[3],
                "buy_cost": row[4],
                "sell_cost": row[5],
            }
            i = i + 1

    return (result_hour_aggr, total_calls, total_duration, total_billsec, total_buy_cost, total_sell_cost)


sqlquery_aggr_country_last24h = """
    SELECT
        country_id,
        SUM(duration) AS duration,
        SUM(billsec) AS billsec,
        SUM(nbcalls) AS nbcalls,
        SUM(buy_cost) AS buy_cost,
        SUM(sell_cost) AS sell_cost
    FROM
        matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('hour', current_timestamp - interval '24' hour) AND
        starting_date <= date_trunc('hour', current_timestamp)
        %(switch)s
    GROUP BY
        country_id
    ORDER BY
        nbcalls DESC, duration DESC
    LIMIT %(limit)s;
    """


def custom_sql_aggr_top_country(switch_id, limit=5):
    """
    perform query to retrieve last 24 hours of aggregate calls data
    """
    result = []
    with connection.cursor() as cursor:
        params = {'switch': condition_switch_id(switch_id), 'limit': limit}
        sqlquery = sqlquery_aggr_country_last24h % params
        cursor.execute(sqlquery)
        rows = cursor.fetchall()
        for row in rows:
            result.append({
                "country_id": row[0],
                "duration": row[1],
                "billsec": row[2],
                "nbcalls": row[3],
                "buy_cost": row[4],
                "sell_cost": row[5],
            })
    return result


sqlquery_aggr_hangup_cause_last24h = """
    SELECT
        hangup_cause_id,
        SUM(duration) as duration,
        SUM(billsec) as billsec,
        SUM(nbcalls) as nbcalls,
        SUM(buy_cost) as buy_cost,
        SUM(sell_cost) as sell_cost
    FROM
        matv_voip_cdr_aggr_hour
    WHERE
        starting_date > date_trunc('hour', current_timestamp - interval '24' hour) and
        starting_date <= date_trunc('hour', current_timestamp)
        %(switch)s
    GROUP BY
        hangup_cause_id
    ORDER BY
        nbcalls, duration DESC
    LIMIT %(limit)s;
    """


def custom_sql_aggr_top_hangup_cause(switch_id=0, limit=10):
    """
    perform query to retrieve last 24 hours of aggregate calls data
    """
    result = {}
    with connection.cursor() as cursor:
        params = {'switch': condition_switch_id(switch_id), 'limit': limit}
        sqlquery = sqlquery_aggr_hangup_cause_last24h % params
        cursor.execute(sqlquery)
        rows = cursor.fetchall()
        i = 0
        for row in rows:
            result[i] = {
                "hangup_cause_id": row[0],
                "duration": row[1],
                "billsec": row[2],
                "nbcalls": row[3],
                "buy_cost": row[4],
                "sell_cost": row[5],
            }
            i = i + 1
    return result
