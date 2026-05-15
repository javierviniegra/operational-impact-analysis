SELECT *
FROM getglobalcashclosing
WHERE subsidiary_id = %(subsidiary_id)s
  AND fecha_corte BETWEEN %(start_date)s AND %(end_date)s;