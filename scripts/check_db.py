
import asyncio
from sqlalchemy import create_engine, inspect
from app.core.config import settings

def check_schema():
    url = "postgresql://dataroom_user:dataroom_password@localhost:5432/dataroom"
    engine = create_engine(url)
    inspector = inspect(engine)
    for table_name in ["folders", "files"]:
        print(f"Table: {table_name}")
        columns = inspector.get_columns(table_name)
        for column in columns:
            print(f" - {column['name']}: {column['type']}")
if __name__ == "__main__":
    check_schema()