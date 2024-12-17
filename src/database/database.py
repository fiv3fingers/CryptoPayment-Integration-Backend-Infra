from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database_models import Base

import os

_database = os.getenv('POSTGRES_DB')
_user = os.getenv('POSTGRES_USER')
_password = os.getenv('POSTGRES_PASSWORD')
_host = os.getenv('POSTGRES_HOST')
_port = os.getenv('POSTGRES_PORT')

engine = create_engine(f'postgresql://{_user}:{_password}@{_host}:{_port}/{_database}')
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base.metadata.create_all(engine)

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
