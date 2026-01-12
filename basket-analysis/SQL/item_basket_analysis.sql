CREATE OR REPLACE TABLE `nowheredata.evaluated_tables.item_basket_analysis`
CLUSTER BY item_id_a, item_id_b
AS

WITH sales_table AS (
SELECT 
     t1.order_id
     , t1.product_id AS item_id
     , COUNT(t1.product_id) OVER(PARTITION BY t1.order_id)  AS items_in_order
  FROM `nowheredata.raw_tables.fact_orders` t1
)

, step_1 AS (
SELECT
     t1.item_id                                   AS item_id_a
     , COALESCE(t2.item_id,t1.item_id)            AS item_id_b
     , COUNT(DISTINCT t1.order_id)                AS order_count
  FROM sales_table t1
  LEFT JOIN sales_table t2
    ON t1.order_id = t2.order_id
   AND t1.item_id  != t2.item_id  
 GROUP BY ALL
 --ORDER BY 1, 3
)

, step_2 AS (
SELECT *
     , SUM(order_count) OVER(PARTITION BY item_id_a)  AS total_orders_item_a
     , SUM(order_count) OVER(PARTITION BY item_id_b)  AS total_orders_item_b
     , SUM(order_count) OVER()                        AS total_orders_company
  FROM step_1
)

, step_3 AS (
SELECT *
     , ROUND(SAFE_DIVIDE(order_count,total_orders_company),4)         AS suport
     , ROUND(SAFE_DIVIDE(order_count,total_orders_item_a),4)          AS confidence
     , ROUND(SAFE_DIVIDE(total_orders_item_b,total_orders_company),4) AS denominator_lift
  FROM step_2
)

SELECT *, ROUND(SAFE_DIVIDE(confidence,denominator_lift),4)   AS lift
  FROM step_3
 WHERE item_id_a <> item_id_b
