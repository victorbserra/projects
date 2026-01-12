WITH percentile_sales AS (
SELECT *
     , CASE WHEN surface < PERCENTILE_CONT(surface, .25) OVER(PARTITION BY microzone) THEN 'Q1'
            WHEN surface < PERCENTILE_CONT(surface, .5)  OVER(PARTITION BY microzone) THEN 'Q2'
            WHEN surface < PERCENTILE_CONT(surface, .75) OVER(PARTITION BY microzone) THEN 'Q3'
       ELSE 'Q4'  END AS quartile_surface
  FROM `methodius-advisory.dw2_cleantables.clean_sales_immobiliare`
 WHERE TRUE
   AND in_auction IS FALSE
   AND class_pricing IN ('priced')
)

, sales AS (
SELECT
     neighborhood
     , microzone
     , property_type
     , quartile_surface
     , ROUND(AVG(surface),2)                    AS avg_sales_surface
     , COUNT(DISTINCT project_id)               AS sales_ads_qty
     , ROUND(AVG(SAFE_DIVIDE(price,surface)),2) AS avg_property_price
  FROM percentile_sales
 GROUP BY ALL
)

, percentile_rent AS (
SELECT *
     , CASE WHEN surface < PERCENTILE_CONT(surface, .25) OVER(PARTITION BY microzone) THEN 'Q1'
            WHEN surface < PERCENTILE_CONT(surface, .5)  OVER(PARTITION BY microzone) THEN 'Q2'
            WHEN surface < PERCENTILE_CONT(surface, .75) OVER(PARTITION BY microzone) THEN 'Q3'
       ELSE 'Q4'  END AS quartile_surface
  FROM `methodius-advisory.dw2_cleantables.clean_rent_immobiliare`
 WHERE TRUE
   AND rent_value IS NOT NULL
)


, rent AS (
SELECT 
     neighborhood
     , microzone
     , property_type
     , quartile_surface
     , ROUND(AVG(surface),2)                   AS avg_rent_surface
     , COUNT(DISTINCT project_id)              AS rent_ads_qty
     , ROUND(AVG(SAFE_DIVIDE(rent_value * 12,surface)),2)           AS avg_yearly_rent_value
  FROM percentile_rent
 WHERE TRUE
 GROUP BY ALL
)


, keys AS (
SELECT DISTINCT * 
  FROM (
    SELECT neighborhood, microzone, property_type,quartile_surface FROM sales
    UNION ALL
    SELECT neighborhood, microzone, property_type,quartile_surface FROM rent
  )
)

, cleaned_data AS (
SELECT 
     keys.neighborhood
     , keys.microzone
     , keys.property_type
     , keys.quartile_surface
     , rent.rent_ads_qty
     , sales.sales_ads_qty
     , ROUND(COALESCE(
          rent.avg_rent_surface
          , AVG(rent.avg_rent_surface) OVER(PARTITION BY keys.neighborhood,keys.microzone,keys.property_type)
          , AVG(rent.avg_rent_surface) OVER(PARTITION BY keys.neighborhood,keys.microzone)
          , AVG(rent.avg_rent_surface) OVER(PARTITION BY keys.neighborhood,keys.property_type)
          , AVG(rent.avg_rent_surface) OVER(PARTITION BY keys.neighborhood)
        ),2)                                                                     AS avg_rent_surface 
     , ROUND(COALESCE(
          sales.avg_sales_surface
          , AVG(sales.avg_sales_surface) OVER(PARTITION BY keys.neighborhood,keys.microzone,keys.property_type)
          , AVG(sales.avg_sales_surface) OVER(PARTITION BY keys.neighborhood,keys.microzone)
          , AVG(sales.avg_sales_surface) OVER(PARTITION BY keys.neighborhood,keys.property_type)
          , AVG(sales.avg_sales_surface) OVER(PARTITION BY keys.neighborhood)
        ),2)                                                                     AS avg_sales_surface
     , ROUND(COALESCE(
          rent.avg_yearly_rent_value
          , AVG(rent.avg_yearly_rent_value) OVER(PARTITION BY keys.neighborhood,keys.microzone,keys.property_type)
          , AVG(rent.avg_yearly_rent_value) OVER(PARTITION BY keys.neighborhood,keys.microzone)
          , AVG(rent.avg_yearly_rent_value) OVER(PARTITION BY keys.neighborhood,keys.property_type)
          , AVG(rent.avg_yearly_rent_value) OVER(PARTITION BY keys.neighborhood)
        ),2)                                                                     AS avg_yearly_rent_value
     , ROUND(COALESCE(
          sales.avg_property_price
          , AVG(sales.avg_property_price) OVER(PARTITION BY keys.neighborhood,keys.microzone,keys.property_type)
          , AVG(sales.avg_property_price) OVER(PARTITION BY keys.neighborhood,keys.microzone)
          , AVG(sales.avg_property_price) OVER(PARTITION BY keys.neighborhood,keys.property_type)
          , AVG(sales.avg_property_price) OVER(PARTITION BY keys.neighborhood)
        ),2)                                                                     AS avg_property_price
  FROM keys
  LEFT JOIN sales
    ON keys.neighborhood  = sales.neighborhood 
   AND keys.microzone     = sales.microzone
   AND keys.property_type = sales.property_type
   AND keys.quartile_surface = sales.quartile_surface
  LEFT JOIN rent
    ON keys.neighborhood  = rent.neighborhood 
   AND keys.microzone     = rent.microzone
   AND keys.property_type = rent.property_type
   AND keys.quartile_surface = rent.quartile_surface
)

SELECT *
     , ROUND(SAFE_DIVIDE(avg_yearly_rent_value,avg_property_price),4) AS return_investiment
  FROM cleaned_data
 ORDER BY 1,2,3,4