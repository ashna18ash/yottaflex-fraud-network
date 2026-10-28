from app.core.database import DATABASE_PATH, engine

print("Database connection setup successful!")
print("Database location:", DATABASE_PATH)

# Test the database connection
with engine.connect() as connection:
    print("SQLite database connection successful!")