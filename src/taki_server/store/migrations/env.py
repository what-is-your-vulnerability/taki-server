from alembic import context
from sqlalchemy import create_engine

from taki_server.store.models import Base

url = context.config.get_main_option("sqlalchemy.url")
if url is None:
    # repo.upgrade_database가 넣는 값이다. 없으면 엉뚱한 DB 대신 바로 멈춘다.
    raise RuntimeError("sqlalchemy.url이 설정되지 않았습니다. repo.upgrade_database(url)로 실행하세요.")
with create_engine(url).connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
    connection.commit()
