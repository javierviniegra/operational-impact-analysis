SELECT *
FROM getallordenesbyday_new_venta
WHERE Sucursal = %(branch_name)s
  AND CAST(Fecha AS DATE) BETWEEN cast(%(start_date)s as DATE) AND cast(%(end_date)s as DATE);