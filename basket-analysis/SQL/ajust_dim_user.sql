ALTER TABLE `nowheredata.raw_tables.dim_users`
ADD COLUMN latitude  FLOAT64,
ADD COLUMN longitude FLOAT64

;

UPDATE `nowheredata.raw_tables.dim_users` u
SET
  latitude  = m.latitude,
  longitude = m.longitude
FROM (
  SELECT 'São Paulo'      AS city_key, -23.6824124 AS latitude, -46.5952992 AS longitude UNION ALL
  SELECT 'Campinas'       AS city_key, -22.8948207 AS latitude, -47.1958509 AS longitude UNION ALL
  SELECT 'Rio de Janeiro' AS city_key, -22.9131580 AS latitude, -43.7756581 AS longitude
) m
WHERE TRIM(u.city) = m.city_key
