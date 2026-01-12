SELECT
     order_id
     , COUNT(order_id)              AS qty_lines
     , COUNT(DISTINCT product_id)   AS qty_items
  FROM `nowheredata.raw_tables.fact_orders`
 GROUP BY ALL
 ORDER BY 2 DESC

;

SELECT 
     DATE_TRUNC(order_date,MONTH)   AS date_ref
     , ROUND(SUM(revenue),2)        AS revenue
  FROM `nowheredata.raw_tables.fact_orders`
 GROUP BY ALL
 ORDER BY 1 DESC

;

---- Base for dash
/* CREATE OR REPLACE TABLE `nowheredata.evaluated_tables.target_analysis` 
PARTITION BY date_ref
CLUSTER BY user_id
AS  */

WITH monthly_sales AS (
SELECT 
     DATE_TRUNC(order_date,MONTH)   AS date_ref
     , user_id
     , ROUND(SUM(revenue),2)        AS revenue
  FROM `nowheredata.raw_tables.fact_orders` 
 WHERE order_id <> 7001094580
 GROUP BY ALL
 --ORDER BY 1 DESC, 3 DESC
)

SELECT t1.*
     , t2.monthly_revenue_target
     , ROUND(AVG(t1.revenue) OVER(PARTITION BY user_id),2) AS avg_store_sales
     , ROUND(AVG(t1.revenue) OVER(
                      PARTITION BY t1.user_id
                      ORDER BY t1.date_ref
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ),2)                                AS AVG_YTD_revenue
     , ROUND(SUM(t1.revenue) OVER(
                      PARTITION BY t1.user_id
                      ORDER BY t1.date_ref
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ),2)                                AS YTD_revenue
     , ROUND(SUM(t2.monthly_revenue_target) OVER(
                      PARTITION BY t1.user_id
                      ORDER BY t1.date_ref
                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ),2)                                AS YTD_target
     , ROUND(t2.monthly_revenue_target * 12)            AS yearly_revenue_target
  FROM monthly_sales t1
  LEFT JOIN `nowheredata.raw_tables.targets` t2 USING(user_id)