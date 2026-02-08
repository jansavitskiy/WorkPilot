# requests.py
from sqlalchemy import select, delete, update, desc, func, cast, Float
from app.database.models import async_session
from app.database.models import User, Info
from datetime import datetime, timedelta


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            new_user = User(tg_id=tg_id, fullname="", password="")
            session.add(new_user)
            await session.commit()
            return new_user
        return user


async def get_user_by_tg_id(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user


async def check_password(tg_id, password):
    """Проверить пароль пользователя"""
    async with async_session() as session:
        user = await session.scalar(
            select(User)
            .where(User.tg_id == tg_id)
            .where(User.password == password)
        )
        return user
    

async def get_work_records_count():
    """Получить количество записей в БД"""
    async with async_session() as session:
        count = await session.scalar(select(func.count(Info.id)))
        return count or 0


async def get_all_users_with_stats():
    """Получить всех пользователей со статистикой"""
    async with async_session() as session:
        result = await session.execute(
            select(
                User.tg_id,
                User.fullname,
                func.count(Info.id).label('total_records'),
                func.sum(cast(Info.hours, Float)).label('total_hours')
            )
            .outerjoin(Info, User.tg_id == Info.user_id)
            .group_by(User.tg_id, User.fullname)
            .order_by(desc(func.count(Info.id)))
        )
        return result.all()


async def get_all_work_with_users():
    """Получить всю информацию о работе с ФИО пользователей"""
    async with async_session() as session:
        result = await session.execute(
            select(
                Info,
                User.fullname
            )
            .join(User, Info.user_id == User.tg_id)
            .order_by(desc(Info.date))
        )
        return result.all()


async def delete_all_work_records():
    """Удалить ВСЕ записи о работе"""
    async with async_session() as session:
        try:
            # Сначала получаем количество записей для отчета
            count = await session.scalar(select(func.count(Info.id)))
            
            # Удаляем все записи
            await session.execute(delete(Info))
            await session.commit()
            
            return count or 0  # Возвращаем сколько удалили
        except Exception as e:
            print(f"Error deleting all records: {e}")
            return 0


async def update_user_fio(tg_id, new_fio):
    async with async_session() as session:
        try:
            user = await session.scalar(
                select(User).where(User.tg_id == tg_id)
            )
            
            if user:
                user.fullname = new_fio
                await session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error updating user FIO: {e}")
            return False


async def update_user_password(tg_id, password):
    """Обновить пароль пользователя"""
    async with async_session() as session:
        try:
            user = await session.scalar(
                select(User).where(User.tg_id == tg_id)
            )
            
            if user:
                user.password = password
                await session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error updating user password: {e}")
            return False


async def register_user(tg_id, fullname, password):
    """Зарегистрировать пользователя (установить ФИО и пароль)"""
    async with async_session() as session:
        try:
            user = await session.scalar(
                select(User).where(User.tg_id == tg_id)
            )
            
            if user:
                # Обновляем существующего пользователя
                user.fullname = fullname
                user.password = password
            else:
                # Создаем нового пользователя
                user = User(tg_id=tg_id, fullname=fullname, password=password)
                session.add(user)
            
            await session.commit()
            return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False


async def get_user_records_count(tg_id):
    async with async_session() as session:
        count = await session.scalar(
            select(func.count(Info.id))
            .where(Info.user_id == tg_id)
        )
        return count or 0


async def save_work_info(user_id, org_name, hours, work_description):
    async with async_session() as session:
        try:
            new_record = Info(
                user_id=user_id,
                org_name=org_name,
                hours=hours,
                work_description=work_description,
                date=datetime.now()
            )
            session.add(new_record)
            await session.commit()
            return True
        except Exception as e:
            print(f"Error saving work info: {e}")
            return False


async def get_last_work_info(user_id):
    async with async_session() as session:
        record = await session.scalar(
            select(Info)
            .where(Info.user_id == user_id)
            .order_by(desc(Info.date))
            .limit(1)
        )
        return record


async def update_work_info(record_id, org_name, hours, work_description):
    async with async_session() as session:
        try:
            record = await session.scalar(
                select(Info).where(Info.id == record_id)
            )
            
            if record:
                record.org_name = org_name
                record.hours = hours
                record.work_description = work_description
                record.date = datetime.now()
                
                await session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error updating work info: {e}")
            return False


async def delete_work_info(record_id):
    async with async_session() as session:
        try:
            record = await session.scalar(
                select(Info).where(Info.id == record_id)
            )
            
            if record:
                await session.delete(record)
                await session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error deleting work info: {e}")
            return False


# UPD: Заметки

async def save_note(user_id, title, content):
    """Сохранить новую заметку"""
    async with async_session() as session:
        try:
            note = Note(user_id=user_id, title=title, content=content, date=datetime.now())
            session.add(note)
            await session.commit()
            return True
        except Exception as e:
            print(f"Error saving note: {e}")
            return False


async def get_user_notes(user_id):
    """Получить все заметки пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Note).where(Note.user_id == user_id).order_by(desc(Note.date))
        )
        return result.scalars().all()


async def delete_note(note_id):
    """Удалить заметку"""
    async with async_session() as session:
        note = await session.scalar(select(Note).where(Note.id == note_id))
        if note:
            await session.delete(note)
            await session.commit()
            return True
        return False
