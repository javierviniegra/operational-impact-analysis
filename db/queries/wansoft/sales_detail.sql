SELECT *
FROM getallordenesbyday_new_detalleventa
WHERE Sucursal = %(branch_name)s
  AND DATE(Hora) BETWEEN %(start_date)s AND %(end_date)s;