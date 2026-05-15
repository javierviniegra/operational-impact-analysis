SELECT *
FROM getinputinventory_entrada
WHERE subsidiary_name = %(subsidiary_id)s
  AND TipoEntrada = 'Factura'
  AND CAST(FechaReal AS DATE) BETWEEN CAST(%(start_date)s AS DATE) AND CAST(%(end_date)s AS DATE);