import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_minjk36vsObF@ep-frosty-sunset-ab8xfub5-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Neon => SSL via sslmode=require dans l'URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

with engine.connect() as conn:
    r = conn.execute(text("select version()")).scalar_one()
    print("Connected to Neon:", r)
