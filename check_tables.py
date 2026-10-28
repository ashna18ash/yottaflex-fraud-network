from sqlalchemy import inspect

from app.core.database import engine


inspector = inspect(engine)

tables = inspector.get_table_names()

print("Tables in fraud_network.db:")
print()

for table in tables:
    print("-", table)

print()
print("Total tables:", len(tables))