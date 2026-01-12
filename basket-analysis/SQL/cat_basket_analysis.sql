CREATE OR REPLACE TABLE `nowheredata.evaluated_tables.category_basket_analysis`
CLUSTER BY item_category_a, item_category_b
AS

WITH sales_table AS (
SELECT 
     t1.order_id
     , prod.category AS item_category
     , COUNT(t1.product_id) OVER(PARTITION BY t1.order_id)
  FROM `nowheredata.raw_tables.fact_orders` t1
  LEFT JOIN `nowheredata.raw_tables.dim_product` prod USING(product_id) 
)

, step_1 AS (
SELECT
     t1.item_category                               AS item_category_a
     , COALESCE(t2.item_category,t1.item_category)  AS item_category_b
     , COUNT(DISTINCT t1.order_id)                  AS order_count
  FROM sales_table t1
  LEFT JOIN sales_table t2
    ON t1.order_id = t2.order_id
   AND t1.item_category != t2.item_category  
 GROUP BY ALL
 --ORDER BY 1, 3
)

, step_2 AS (
SELECT *
     , SUM(order_count) OVER(PARTITION BY item_category_a)  AS total_orders_cat_a
     , SUM(order_count) OVER(PARTITION BY item_category_b)  AS total_orders_cat_b
     , SUM(order_count) OVER()                              AS total_orders_company
  FROM step_1
)

, step_3 AS (
SELECT *
     , ROUND(SAFE_DIVIDE(order_count,total_orders_company),4)         AS suport
     , ROUND(SAFE_DIVIDE(order_count,total_orders_cat_a),4)           AS confidence
     , ROUND(SAFE_DIVIDE(total_orders_cat_b,total_orders_company),4)  AS denominator_lift
  FROM step_2
)

SELECT *, ROUND(SAFE_DIVIDE(confidence,denominator_lift),4)   AS lift
  FROM step_3
 WHERE item_category_a != item_category_b