{% macro map_active(column_name) %}
    CASE
        WHEN {{column_name}} = 'Active' THEN true
        WHEN {{column_name}} = 'Not-active' THEN false
        ELSE false
    END
{% endmacro %}