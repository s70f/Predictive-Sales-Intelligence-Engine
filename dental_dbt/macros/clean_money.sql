{% macro clean_money(column_name) %}
    CAST(
        NULLIF(
            REPLACE(
                REPLACE({{ column_name }}, '$', ''),
                '#N/A', ''
            ),
            ''
        )
        AS NUMERIC(10, 2)
    )
{% endmacro %}