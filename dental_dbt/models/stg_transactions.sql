{{ config(materialized='table') }} -- command for dbt engine to wrap query in CREATE TABLE AS

SELECT
    "Order Num" AS order_id, -- Note: Must use double quotes or postgres qill think order num is two commands.
    "Customer" AS clinic_name,
    "Item Code" AS item_code,
    "Item Name" AS item_name,
    "Qty" AS quantity,

    CAST("Date" AS DATE) AS transaction_date,

    -- Using Macro
    {{ clean_money('"Sales Price"')}} AS unit_price,
    {{ clean_money('"Cost"')}} AS unit_cost,
    "Amount" AS total_revenue

FROM {{ source('external_data', 'raw_transacations') }} -- Keeps all the file names in one file for easy change

-- FROM {{ ref('raw_transacations')}} -- don't hardcode table name. This references file in seed folder
