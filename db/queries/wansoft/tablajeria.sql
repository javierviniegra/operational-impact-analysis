SELECT *
FROM gettablajeriareport
WHERE subsidiary_id = %(subsidiary_id)s
  AND InputDate BETWEEN %(start_date)s AND %(end_date)s;