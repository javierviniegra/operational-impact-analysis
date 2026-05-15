SELECT *
FROM submissions
WHERE location_name = %(location_name)s
  AND date_submitted BETWEEN %(start_date)s AND %(end_date)s;