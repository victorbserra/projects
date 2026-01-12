WITH sales AS (
SELECT
     neighborhood
     , microzone
     , property_type
     , COUNT(DISTINCT project_id)               AS sales_ads_qty
     , ROUND(AVG(price),2)                      AS avg_property_price
  FROM `methodius-advisory.dw2_cleantables.clean_sales_immobiliare`
 WHERE TRUE
   AND in_auction IS FALSE
   AND class_pricing IN ('priced')
 GROUP BY ALL
)

, rent AS (
SELECT 
     neighborhood
     , microzone
     , property_type
     , COUNT(DISTINCT project_id)              AS rent_ads_qty
     , ROUND(AVG(rent_value * 12),2)           AS avg_yearly_rent_value
  FROM `methodius-advisory.dw2_cleantables.clean_rent_immobiliare`
 WHERE TRUE
   AND rent_value IS NOT NULL
 GROUP BY ALL
)


, keys AS (
SELECT DISTINCT * 
  FROM (
    SELECT neighborhood, microzone, property_type FROM sales
    UNION ALL
    SELECT neighborhood, microzone, property_type FROM rent
  )
)

SELECT 
     keys.neighborhood
     , keys.microzone
     , keys.property_type
     , rent_ads_qty
     , sales_ads_qty
     , avg_yearly_rent_value
     , avg_property_price
     , ROUND(SAFE_DIVIDE(avg_yearly_rent_value,avg_property_price),4) AS revenue
  FROM keys
 LEFT JOIN sales
   ON keys.neighborhood  = sales.neighborhood 
  AND keys.microzone     = sales.microzone
  AND keys.property_type = sales.property_type
  LEFT JOIN rent
   ON keys.neighborhood  = rent.neighborhood 
  AND keys.microzone     = rent.microzone
  AND keys.property_type = rent.property_type