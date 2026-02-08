from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine, expire_on_commit=False)  # Изменил имя на async_session


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    fullname: Mapped[str] = mapped_column(String(100), nullable=True)  # Добавил nullable=True
    password: Mapped[str] = mapped_column(String(100), nullable=True)  # Добавил nullable=True


class Info(Base):
    __tablename__ = 'work_info'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)  # tg_id сотрудника
    org_name: Mapped[str] = mapped_column(String(125)) # Название организации
    hours: Mapped[str] = mapped_column(String(50))  # Часы работы
    work_description: Mapped[str] = mapped_column(Text)  # Описание работы
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)  # Дата записи



async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

#UPD модель заметок
class Note(Base):
    __tablename__ = 'notes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
         