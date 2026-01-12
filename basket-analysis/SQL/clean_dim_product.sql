CREATE OR REPLACE TABLE `nowheredata.evaluated_tables.dim_product` 
CLUSTER BY product_id
AS

SELECT
     t1.product_id
     , t1.category AS category_item
     , t4.sales_per_day
     , t4.sales_2024
     , t2.frequency_items
     , t2.median_frequency
     , t2.share_of_wallet
     , t2.median_share_of_wallet
     , t2.classification_items
     , t3.community AS original_cluster_id
     , CASE WHEN t3.community IN (0, 2, 7, 9) THEN 1
            WHEN t3.community IN (4, 11)      THEN 2
            WHEN t3.community IN (5, 8)       THEN 3
            WHEN t3.community = 3             THEN 4
            WHEN t3.community = 1             THEN 5
            WHEN t3.community = 10            THEN 6
            WHEN t3.community = 6             THEN 7
        END AS cluster_index
     , CASE WHEN t3.community IN (0, 2, 7, 9) THEN 'Stockup Beer'
            WHEN t3.community IN (4, 11)      THEN 'Casual Beer'
            WHEN t3.community IN (5, 8)       THEN 'Home Cocktail'
            WHEN t3.community = 3             THEN 'Social Drinks'
            WHEN t3.community = 1             THEN 'Mixed Basket'
            WHEN t3.community = 10            THEN 'Beverage Replenishment'
            WHEN t3.community = 6             THEN 'Non Alcoholic'
        END AS cluster_name
     , t3.macro_community
     , CASE t3.macro_community WHEN 0 THEN 'CORE BASKET'
                               WHEN 1 THEN 'IMPULSE BASKET'
        END AS macro_community_description
  FROM `nowheredata.raw_tables.dim_product` t1
  LEFT JOIN `nowheredata.evaluated_tables.item_classification`  t2 ON t1.product_id = t2.product_id
  LEFT JOIN `nowheredata.evaluated_tables.clusterization_items` t3 ON t1.product_id = t3.product_id
  LEFT JOIN (
      SELECT 
      product_id, ROUND(SUM(revenue),2) AS sales_2024
      , ROUND(SAFE_DIVIDE(SUM(revenue),COUNTIF(revenue > 0)),2) AS sales_per_day
    FROM `nowheredata.raw_tables.fact_orders` 
   WHERE order_id <> 7001094580
   GROUP BY ALL
  ) t4 ON t1.product_id = t4.product_id
 WHERE t2.frequency_items IS NOT NULL



