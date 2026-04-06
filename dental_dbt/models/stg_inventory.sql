{{ config(materialized='table') }}

SELECT
    
    CAST("Item" AS VARCHAR(50)) AS item_code,
    "Description" AS item_name,
    "Type" AS category,
    COALESCE(CAST("Quantity On Hand" AS INTEGER), 0) AS stock_level,
    
    "Price" AS unit_price,
    "Gross Price" AS gross_price,
    "Cost" AS unit_cost,
    
    {{ map_active('"Active Status"')}} AS active_status

FROM {{ source('external_data', 'raw_inventory') }}
