SELECT *
FROM costeomensual
WHERE subsidiary_id = %(subsidiary_id)s
  AND mes_ano BETWEEN %(start_month)s AND %(end_month)s;