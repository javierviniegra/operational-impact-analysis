SELECT *
FROM getallordenesbyday_new_pago
WHERE Sucursal = %(branch_name)s
  AND DATE(Fecha) BETWEEN %(start_date)s AND %(end_date)s;