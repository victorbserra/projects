CREATE OR REPLACE TABLE `nowheredata.evaluated_tables.item_classification` AS

WITH base AS (
SELECT
     order_id
     , product_id
     , SUM(revenue) AS revenue
  FROM `nowheredata.raw_tables.fact_orders`
 WHERE order_id <> 7001094580
 GROUP BY ALL
)

, frequency AS (
SELECT 
     product_id
     , ROUND(SUM(revenue))               AS sales_item
     , (SELECT SUM(revenue) FROM base)   AS total_sales
     , COUNT(DISTINCT order_id)                    AS orders_with_item
     , (SELECT COUNT(DISTINCT order_id) FROM base) AS total_orders
  FROM base
 GROUP BY ALL
)

--SELECT *, ROUND(SAFE_DIVIDE(orders_with_item,total_orders),4) FROM frequency

, order_items AS (
SELECT
     order_id
     , COUNT(DISTINCT product_id) AS items_in_order
     , SUM(revenue)               AS revenue_in_order
  FROM base
 GROUP BY ALL
)

, sow_tbl AS (
SELECT
     t1.order_id
     , t1.product_id
     , t1.revenue
     , t2.items_in_order
     , t2.revenue_in_order
     , ROUND(SAFE_DIVIDE(1,t2.items_in_order),3)            AS perc_qty_share_of_wallet
     , ROUND(SAFE_DIVIDE(t1.revenue,t2.revenue_in_order),3) AS perc_revenue_share_of_wallet
  FROM base t1 
  LEFT JOIN order_items t2
    ON t1.order_id = t2.order_id
)

, final_sow_tbl AS (
SELECT
     product_id
     , ROUND(AVG(perc_revenue_share_of_wallet),4) AS share_of_wallet
  FROM sow_tbl
 GROUP BY ALL
)

, join_tbl AS (
SELECT
     t1.product_id
     , ROUND(SAFE_DIVIDE(t1.orders_with_item, t1.total_orders),4) AS frequency_items
     , t2.share_of_wallet
  FROM frequency t1
  LEFT JOIN final_sow_tbl t2 USING(product_id)
)

, step_1 AS (
SELECT t1.*
     , prod.category                                           AS category_item
     , ROUND(PERCENTILE_CONT(t1.frequency_items, .5) OVER(),4) AS median_frequency
     , ROUND(PERCENTILE_CONT(t1.share_of_wallet, .5) OVER(),4) AS median_share_of_wallet
  FROM join_tbl t1
  LEFT JOIN `nowheredata.raw_tables.dim_product` prod USING(product_id)
)

SELECT *
     , CASE WHEN frequency_items >= median_frequency AND share_of_wallet >= median_share_of_wallet THEN 'DESTINATION'
            WHEN frequency_items >= median_frequency AND share_of_wallet <  median_share_of_wallet THEN 'TRAFFIC DRIVER'
            WHEN frequency_items <  median_frequency AND share_of_wallet >= median_share_of_wallet THEN 'VALUE DRIVER'
            WHEN frequency_items <  median_frequency AND share_of_wallet <  median_share_of_wallet THEN 'COMPLEMENTARY'
        END    AS classification_items
  FROM step_1


