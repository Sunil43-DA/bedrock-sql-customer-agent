
from sql_engine import execute_query

query = """
    SELECT ROUND(AVG(total_spend), 2) AS average_spend
    FROM customers
"""

result = execute_query(query)

print(result.to_string(index=False))
