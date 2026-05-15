SELECT *
FROM zenput_tasks
WHERE account_name = %(account_name)s
  AND date_due BETWEEN %(start_date)s AND %(end_date)s;