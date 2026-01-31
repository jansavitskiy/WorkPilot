import io
import os
import csv
from datetime import datetime
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import BufferedInputFile, FSInputFile

from app.states import Registration, LoginState, AdminPassword, Info, EditInfo, DeleteConfirm, Profile, OrgStates, OrganizationStates
import app.buttons as kb
import app.database.requests as rq
from app.utils import orgs, org_manager, get_organizations_file
from api import admin_password

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer("Добро пожаловать в бот. Для начала зарегистрируйтесь",
                         reply_markup=kb.start_menu)


@router.callback_query(F.data == "registration")
async def reg(callback: CallbackQuery, state: FSMContext):
    # Проверяем, не зарегистрирован ли уже пользователь
    user = await rq.get_user_by_tg_id(callback.from_user.id)
    if user and user.fullname and user.password:
        await callback.message.answer(
            "Вы уже зарегистрированы! Используйте кнопку 'Войти'.",
            reply_markup=kb.start_menu
        )
        await callback.answer()
        return
    
    await state.set_state(Registration.fullname)
    await callback.message.answer("Введите ваше полное ФИО:")
    await callback.answer()


@router.message(Registration.fullname)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await state.set_state(Registration.password1)  
    await message.answer("Введите свой пароль:")  


@router.message(Registration.password1)
async def reg_pass1(message: Message, state: FSMContext):
    await state.update_data(password1=message.text)
    await state.set_state(Registration.password2)  
    await message.answer("Введите свой пароль повторно:") 


@router.message(Registration.password2)
async def reg_pass2(message: Message, state: FSMContext):
    data = await state.get_data()
    password1 = data.get('password1')
    password2 = message.text
    fullname = data.get('fullname')
    
    if password1 == password2:
        # Сохраняем данные в БД
        success = await rq.register_user(
            tg_id=message.from_user.id,
            fullname=fullname,
            password=password1
        )
        
        if success:
            await message.answer(f"{fullname}, вы успешно зарегистрировались в панели сотрудника",
                                 reply_markup=kb.personal_menu)
        else:
            await message.answer("Ошибка при регистрации. Попробуйте снова.",
                                 reply_markup=kb.start_menu)
    else:
        await message.answer("Пароли не совпадают. Попробуйте снова.",
                             reply_markup=kb.start_menu)
    
    await state.clear()


@router.callback_query(F.data == "login")
async def login_start(callback: CallbackQuery, state: FSMContext):
    # Проверяем, зарегистрирован ли пользователь
    user = await rq.get_user_by_tg_id(callback.from_user.id)
    
    if not user or not user.fullname or not user.password:
        await callback.message.answer(
            "Вы еще не зарегистрированы! Пожалуйста, сначала зарегистрируйтесь.",
            reply_markup=kb.start_menu
        )
        await callback.answer()
        return
    
    await state.set_state(LoginState.password)
    await callback.message.answer("Введите пароль для входа в панель сотрудника:")
    await callback.answer()


@router.message(LoginState.password)
async def login_check_password(message: Message, state: FSMContext):
    password = message.text
    tg_id = message.from_user.id
    
    # Проверяем пароль
    user = await rq.check_password(tg_id, password)
    
    if user:
        await message.answer(f"Добро пожаловать в панель сотрудника, {user.fullname}!",
                             reply_markup=kb.personal_menu)
    else:
        await message.answer("Неверный пароль! Попробуйте снова.",
                             reply_markup=kb.start_menu)
    
    await state.clear()


@router.callback_query(F.data == "admin_panel")
async def admin_control(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminPassword.adpassword)
    await callback.message.answer("🔐 Чтобы войти в админ-панель введите пароль: ")
    await callback.answer()


@router.message(AdminPassword.adpassword)
async def admin(message: Message, state: FSMContext):
    password = message.text.strip()  
    
    if password == admin_password:  # Проверяем пароль
        # Получаем статистику
        records_count = await rq.get_work_records_count()
        
        await message.answer(
            f"✅ *Добро пожаловать в панель администратора!*\n\n"
            f"*Доступные функции:*\n"
            f"1. 📊 Получить отчет в Excel\n"
            f"2. 👥 Посмотреть сотрудников\n"
            f"3. 🗑️ Удалить все записи (после отчета)\n"
            f"4. 📈 Посмотреть статистику",
            parse_mode="Markdown",
            reply_markup=kb.admin_menu
        )
    else:
        await message.answer("❌ Вы ввели неверный пароль!")
    
    await state.clear()


@router.callback_query(F.data == "work_info")
async def info_about_work(callback: CallbackQuery):
    await callback.message.answer(
        "📝 Здесь вы можете оставить отчёт о своей проделанной работе за день", 
        reply_markup=kb.info_menu
    )
    await callback.answer()


# Новый обработчик для начала записи информации
@router.callback_query(F.data == "insert_info")
async def start_insert_info(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Info.org)
    await callback.message.answer(
        "🏢 Введите название организации, с которой работали:"
    )
    await callback.answer()


# Обработчик для ввода названия организации
@router.message(Info.org)
async def process_org_name(message: Message, state: FSMContext):
    await state.update_data(org=message.text)
    await state.set_state(Info.hours)
    await message.answer(
        "⏰ Введите количество часов, которые вы работали с этим клиентом\n"
        "Пример: 4.5 или 8"
    )


# Обработчик для ввода часов
@router.message(Info.hours)
async def process_hours(message: Message, state: FSMContext):
    # Простая валидация часов (можно улучшить)
    try:
        hours = message.text.replace(',', '.')
        float(hours)  # Проверяем, что это число
        await state.update_data(hours=message.text)
        await state.set_state(Info.work)
        await message.answer(
            "📋 Опишите проделанную работу:\n"
            "• Какие задачи выполнили\n"
            "• Результаты\n"
            "• Проблемы и решения\n\n"
            "Можете писать подробно:"
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число (например: 4.5 или 8):"
        )


# Обработчик для ввода описания работы и сохранения в БД
@router.message(Info.work)
async def process_work_description(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем информацию в БД
    success = await rq.save_work_info(
        user_id=message.from_user.id,
        org_name=data.get('org'),
        hours=data.get('hours'),
        work_description=message.text
    )
    
    if success:
        await message.answer(
            f"✅ Информация успешно сохранена!\n\n"
            f"🏢 Организация: {data.get('org')}\n"
            f"⏰ Часы: {data.get('hours')}\n"
            f"Запись сохранена в базе данных.",
            reply_markup=kb.info_menu
        )
    else:
        await message.answer(
            "❌ Ошибка при сохранении информации. Попробуйте снова.",
            reply_markup=kb.info_menu
        )
    
    await state.clear()


@router.callback_query(F.data == "org_list")
async def send_organizations(callback: CallbackQuery):
    """Отправить файл со списком организаций"""
    try:
        # Получаем файл
        file_path = get_organizations_file()
        
        if file_path and file_path.exists():
            # Отправляем файл
            document = FSInputFile(
                path=file_path,
                filename="organizations.xlsx"
            )
            
            # Получаем статистику
            orgs_count = len(org_manager.get_all_orgs())
            
            await callback.message.answer_document(
                document=document,
                caption=f"📋 Файл со списком организаций\n\nВсего организаций: {orgs_count}"
            )
            
            # Показываем дополнительное меню
            await callback.message.answer(
                "Если вашей организации нет в списке, вы можете её добавить:",
                reply_markup=kb.new_org_menu
            )
            
            # Удаляем временный файл после отправки
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await callback.message.answer(
                "📭 Список организаций пока пуст.\n"
                "Вы можете добавить первую организацию:",
                reply_markup=kb.new_org_menu
            )
        
        await callback.answer()
        
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")
        await callback.answer()


@router.callback_query(F.data == "newOrga")
async def start_add_organization(callback: CallbackQuery, state: FSMContext):
    """Начать процесс добавления новой организации"""
    await callback.message.answer(
        "✏️ Введите название новой организации:\n\n"
        "Примеры:\n"
        "• ООО 'Ромашка'\n"
        "• ИП Иванов И.И.\n"
        "• АО 'Строительные технологии'",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(OrganizationStates.waiting_for_org_name)
    await callback.answer()


@router.message(OrganizationStates.waiting_for_org_name)
async def process_organization_name(message: Message, state: FSMContext):
    """Обработать введенное название организации"""
    org_name = message.text.strip()
    
    # Валидация
    if len(org_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите еще раз:", reply_markup=kb.cancel_kb)
        return
    
    if len(org_name) > 100:
        await message.answer("❌ Название слишком длинное. Введите до 100 символов:", reply_markup=kb.cancel_kb)
        return
    
    # Добавляем организацию
    user_name = message.from_user.full_name or f"Сотрудник ID:{message.from_user.id}"
    success, result_message = org_manager.check_and_add_org(org_name, user_name)
    
    if success:
        # Обновляем кэшированный файл (если есть)
        org_manager.cleanup_temp_files()
        
        await message.answer(
            f"✅ {result_message}\n\n"
            f"Организация <b>'{org_name}'</b> теперь доступна в общем списке.\n"
            f"Вы можете найти её в файле с организациями.",
            reply_markup=kb.cancel_kb
        )
    else:
        await message.answer(
            f"❌ {result_message}\n\n"
            "Попробуйте ввести другое название организации:",
            reply_markup=kb.cancel_kb
        )
    
    await state.clear()


# Обработчик отмены
@router.callback_query(F.data == "cancel_org")
async def cancel_organization(callback: CallbackQuery, state: FSMContext):
    """Отменить добавление организации"""
    await state.clear()
    await callback.message.answer("❌ Добавление организации отменено")
    await callback.message.answer("Выберите действие:", reply_markup=kb.new_org_menu)
    await callback.answer()



# Команда для админа для просмотра списка
@router.message(Command("org_list"))
async def show_organizations_list(message: Message):
    """Показать список организаций (для админов)"""
    # Проверка прав админа
    if message.from_user.id not in "Zy2007br":  # Замените на свою проверку
        return
    
    orgs_text = org_manager.get_formatted_list(limit=20)
    await message.answer(orgs_text)


# Обработчик для просмотра последней записи
@router.callback_query(F.data == "last_info")
async def show_last_info(callback: CallbackQuery):
    # Получаем последнюю запись пользователя
    last_record = await rq.get_last_work_info(callback.from_user.id)
    
    if last_record:
        await callback.message.answer(
            f"📋 Ваша последняя запись:\n\n"
            f"🏢 Организация: {last_record.org_name}\n"
            f"⏰ Часы: {last_record.hours}\n"
            f"📅 Дата: {last_record.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📝 Описание:\n{last_record.work_description}\n\n"
            f"Хотите изменить или удалить запись?",
            reply_markup=kb.last_info_menu
        )
    else:
        await callback.message.answer(
            "📭 У вас пока нет сохранённых записей о работе.",
            reply_markup=kb.info_menu
        )
    
    await callback.answer()


@router.callback_query(F.data == "edit_info")
async def start_edit_info(callback: CallbackQuery, state: FSMContext):
    # Получаем последнюю запись пользователя
    last_record = await rq.get_last_work_info(callback.from_user.id)
    
    if not last_record:
        await callback.message.answer("❌ У вас нет записей для редактирования.")
        await callback.answer()
        return
    
    # Сохраняем ID записи для редактирования
    await state.update_data(edit_record_id=last_record.id)
    await state.set_state(EditInfo.edit_org)
    
    await callback.message.answer(
        f"✏️ Редактирование записи от {last_record.date.strftime('%d.%m.%Y')}\n\n"
        f"Текущая организация: {last_record.org_name}\n"
        f"Введите новое название организации:"
    )
    await callback.answer()


@router.message(EditInfo.edit_org)
async def process_edit_org(message: Message, state: FSMContext):
    await state.update_data(edit_org=message.text)
    await state.set_state(EditInfo.edit_hours)
    
    # Получаем текущую запись для показа текущих часов
    last_record = await rq.get_last_work_info(message.from_user.id)
    
    await message.answer(
        f"Текущие часы: {last_record.hours}\n"
        f"Введите новое количество часов:"
    )


@router.message(EditInfo.edit_hours)
async def process_edit_hours(message: Message, state: FSMContext):
    # Проверяем, что введено число
    try:
        hours = message.text.replace(',', '.')
        float(hours)
        await state.update_data(edit_hours=message.text)
        await state.set_state(EditInfo.edit_work)
        
        await message.answer(
            "Введите новое описание работы:"
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число (например: 4.5 или 8):"
        )


@router.message(EditInfo.edit_work)
async def process_edit_work(message: Message, state: FSMContext):
    data = await state.get_data()
    record_id = data.get('edit_record_id')
    
    # Обновляем запись в БД
    success = await rq.update_work_info(
        record_id=record_id,
        org_name=data.get('edit_org'),
        hours=data.get('edit_hours'),
        work_description=message.text
    )
    
    if success:
        await message.answer(
            "✅ Запись успешно обновлена!",
            reply_markup=kb.info_menu
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении записи.",
            reply_markup=kb.info_menu
        )
    
    await state.clear()


@router.callback_query(F.data == "delete_info")
async def delete_info(callback: CallbackQuery, state: FSMContext):
    last_record = await rq.get_last_work_info(callback.from_user.id)
    
    if not last_record:
        await callback.callback.message.answer("❌ У вас нет записей для удаления.")
        await callback.answer()
        return
    
    # Сохраняем ID записи для удаления
    await state.update_data(delete_record_id=last_record.id)
    await state.set_state(DeleteConfirm.confirm)
    
    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить эту запись?\n\n"
        f"Дата: {last_record.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Организация: {last_record.org_name}\n"
        f"Часы: {last_record.hours}\n\n"
        f"Напишите 'ДА' для подтверждения или 'НЕТ' для отмены:"
    )
    await callback.answer()


@router.message(DeleteConfirm.confirm)  # Это должно обрабатывать сообщения, а не callback
async def confirm_delete(message: Message, state: FSMContext):
    user_input = message.text.strip().upper()
    data = await state.get_data()
    record_id = data.get('delete_record_id')
    
    if user_input == 'ДА':
        # Удаляем запись из БД
        success = await rq.delete_work_info(record_id)
        
        if success:
            await message.answer(
                "✅ Запись успешно удалена!",
                reply_markup=kb.info_menu
            )
        else:
            await message.answer(
                "❌ Ошибка при удалении записи.",
                reply_markup=kb.info_menu
            )
    elif user_input == 'НЕТ':
        await message.answer(
            "❌ Удаление отменено.",
            reply_markup=kb.info_menu
        )
    else:
        await message.answer(
            "Пожалуйста, напишите 'ДА' или 'НЕТ':"
        )
        return  # Не очищаем состояние
    
    await state.clear()
    

@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    # Получаем данные пользователя из БД
    user = await rq.get_user_by_tg_id(callback.from_user.id)
    
    if user and user.fullname:
        await callback.message.answer(
            f"👤 *Вот вся информация о вашем профиле*\n\n"
            f"🆔 ID: {callback.from_user.id}\n"
            f"📛 ФИО: {user.fullname}\n",
            parse_mode="Markdown",
            reply_markup=kb.profile_settings
        )
    else:
        await callback.message.answer(
            "❌ Вы еще не зарегистрированы!",
            reply_markup=kb.start_menu
        )
    
    await callback.answer()


@router.callback_query(F.data == "change_fio")
async def start_change_fio(callback: CallbackQuery, state: FSMContext):
    # Получаем текущие данные пользователя
    user = await rq.get_user_by_tg_id(callback.from_user.id)
    
    if not user:
        await callback.message.answer("❌ Сначала нужно зарегистрироваться!")
        await callback.answer()
        return
    
    await state.set_state(Profile.new_fio)
    await callback.message.answer(
        f"✏️ *Изменение ФИО*\n\n"
        f"Текущее ФИО: {user.fullname if user.fullname else 'Не установлено'}\n\n"
        f"Введите новое ФИО:",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Profile.new_fio)
async def process_change_fio(message: Message, state: FSMContext):
    new_fio = message.text.strip()
    
    if len(new_fio) < 2:
        await message.answer("❌ ФИО слишком короткое! Минимум 2 символа.")
        return
    
    # Обновляем ФИО в базе данных
    success = await rq.update_user_fio(
        tg_id=message.from_user.id,
        new_fio=new_fio
    )
    
    if success:
        await message.answer(
            f"✅ ФИО успешно изменено на: *{new_fio}*",
            parse_mode="Markdown",
            reply_markup=kb.profile_settings
        )
    else:
        await message.answer(
            "❌ Ошибка при изменении ФИО. Попробуйте позже.",
            reply_markup=kb.profile_settings
        )
    
    await state.clear()


@router.callback_query(F.data == "get_organization")
async def org_main(callback: CallbackQuery):
    """Главное меню организаций"""
    count = len(orgs.get_all_orgs())
    
    text = f"🏢 Управление организациями\n\nВсего организаций в списке сейчас: {count}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть список", callback_data="view_orgs")],
            [InlineKeyboardButton(text="➕ Добавить", callback_data="add_org")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_org")],
            [InlineKeyboardButton(text="📥 Скачать файл", callback_data="download_orgs")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel1")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# Посмотреть список
@router.callback_query(F.data == "view_orgs")
async def view_organizations(callback: CallbackQuery):
    """Показать список организаций"""
    org_list = orgs.get_all_orgs()
    
    if not org_list:
        text = "📭 Список пуст"
    else:
        text = "📋 Список организаций:\n\n"
        for i, org in enumerate(org_list, 1):
            text += f"{i}. {org}\n"
    
    
    await callback.message.edit_text(text, reply_markup=kb.back_admin_keyboard)


# Добавить организацию
@router.callback_query(F.data == "add_org")
async def add_org_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление"""
    await callback.message.edit_text("Введите название новой организации:")
    await state.set_state(OrgStates.adding)


@router.message(OrgStates.adding)
async def add_org_finish(message: Message, state: FSMContext):
    """Завершить добавление"""
    name = message.text.strip()
    
    if not name:
        await message.answer("❌ Название не может быть пустым!",
                             reply_markup=kb.back_admin_keyboard)
        return
    
    if orgs.add_org(name):
        await message.answer(f"✅ Добавлено: {name}",
                             reply_markup=kb.back_admin_keyboard)
    else:
        await message.answer("❌ Ошибка при добавлении")
    
    await state.clear()

# Удалить организацию
@router.callback_query(F.data == "delete_org")
async def delete_org_start(callback: CallbackQuery, state: FSMContext):
    """Начать удаление"""
    org_list = orgs.get_all_orgs()
    
    if not org_list:
        await callback.message.edit_text("📭 Список организаций пуст")
        return
    
    text = "Введите название организации для удаления:\n\n"
    for org in org_list:
        text += f"• {org}\n"
    
    await callback.message.edit_text(text)
    await state.set_state(OrgStates.deleting)


@router.message(OrgStates.deleting)
async def delete_org_finish(message: Message, state: FSMContext):
    """Завершить удаление"""
    name = message.text.strip()
    
    if orgs.delete_org(name):
        await message.answer(f"✅ Удалено: {name}",
                             reply_markup=kb.back_admin_keyboard)
    else:
        await message.answer(f"❌ Организация '{name}' не найдена",
                             reply_markup=kb.back_admin_keyboard)
    
    await state.clear()


# Скачать файл
@router.callback_query(F.data == "download_orgs")
async def download_orgs_file(callback: CallbackQuery):
    """Скачать Excel файл"""
    excel_file = orgs.export_excel()
    
    if excel_file:
        await callback.message.answer_document(
            BufferedInputFile(
                excel_file.read(),
                filename="organizations.xlsx"
            ),
            caption="📁 Файл со списком организаций"
        )
        await callback.message.answer("Посмотрите этот список, если надо, то вы можете его изменить",
                                      reply_markup=kb.back_admin_keyboard)
    else:
        await callback.message.answer("📭 Нет организаций для экспорта",
                                      reply_markup=kb.back_admin_keyboard)


@router.callback_query(F.data == "admin_get_report")
async def admin_get_report(callback: CallbackQuery):
    """Создать и отправить CSV отчет для Excel"""
    records = await rq.get_all_work_with_users()
    
    if not records:
        await callback.message.answer("📭 В базе данных нет записей для отчета.")
        await callback.answer()
        return
    
    processing_msg = await callback.message.answer("⏳ Создаю Excel отчет...")
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    
    # Заголовки
    writer.writerow([
        "Работа сотрудников"
    ])
    
    total_hours = 0
    for info, fullname in records:
        # Очищаем текст для CSV
        clean_desc = info.work_description.replace('\n', ' ').replace('\r', ' ')
        
        writer.writerow([
            fullname or 'Не указано',
            info.org_name,
            info.hours,
            clean_desc,
            info.date.strftime('%d.%m.%Y %H:%M')
        ])
        
        try:
            total_hours += float(info.hours)
        except:
            pass
    
    # Получаем байты в UTF-8 с BOM для Excel
    csv_bytes = output.getvalue().encode('utf-8-sig')
    
    filename = f"отчет_работа_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    # Отправляем файл
    await callback.message.answer_document(
        document=BufferedInputFile(
            file=csv_bytes,
            filename=filename
        ),
        caption=(
            f"📊 *ОТЧЕТ В ФОРМАТЕ CSV*\n\n"
            f"📋 Записей: *{len(records)}*\n"
            f"⏰ Всего часов: *{total_hours:.1f}*\n"
            f"📅 Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"💡 *Откройте в Excel или Google Таблицах*"
        ),
        parse_mode="Markdown",
        reply_markup=kb.after_report_keyboard
    )
    
    await processing_msg.delete()
    await callback.answer()


@router.callback_query(F.data == "admin_users_list")
async def show_users_list(callback: CallbackQuery):
    """Показать список всех сотрудников"""
    users_stats = await rq.get_all_users_with_stats()
    
    if not users_stats:
        await callback.message.answer(
            "👥 В базе нет зарегистрированных сотрудников.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
                ]
            )
        )
        await callback.answer()
        return
    
    report_lines = [
        "👥 *СПИСОК СОТРУДНИКОВ*",
        f"📊 Всего: {len(users_stats)} человек",
        "=" * 40 + "\n"
    ]
    
    for user in users_stats:
        report_lines.append(
            f"👤 *{user.fullname or 'Без ФИО'}*\n"
            f"   🆔 ID: {user.tg_id}\n"
            f"   📊 Записей: {user.total_records or 0}\n"
            f"   ⏰ Часов: {user.total_hours or 0}\n"
        )
    
    await callback.message.answer(
    "\n".join(report_lines),
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ]
    )
)


@router.callback_query(F.data == "admin_clear_records")
async def admin_clear_records(callback: CallbackQuery):
    """Прямой переход к удалению записей"""
    records_count = await rq.get_work_records_count()
    
    if records_count == 0:
        await callback.message.answer(
            "📭 В базе данных нет записей для удаления.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
                ]
            )
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"🗑️ *Удаление записей о работе*\n\n"
        f"В базе данных: *{records_count}* записей\n\n"
        f"*Рекомендуется сначала получить отчет,*\n"
        f"*а потом удалять записи.*\n\n"
        f"Что вы хотите сделать?",
        parse_mode="Markdown",
        reply_markup=kb.confirm_delete_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin_clear_after_report")
async def admin_clear_after_report(callback: CallbackQuery):
    """Подтверждение удаления записей после получения отчета"""
    records_count = await rq.get_work_records_count()
    
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ ДА, удалить", callback_data="admin_confirm_clear"),
                InlineKeyboardButton(text="❌ НЕТ, оставить", callback_data="admin_panel")
            ]
        ]
    )
    
    # Вместо edit_text используем answer для нового сообщения
    await callback.message.answer(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы получили отчет с *{records_count}* записей.\n"
        f"Удалить все записи из базы данных?\n\n"
        f"*Это действие очистит таблицу с записями о работе.*\n"
        f"*Данные сотрудников (логины/пароли) останутся нетронутыми.*",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin_clear_records")
async def admin_clear_records(callback: CallbackQuery):
    """Прямой переход к удалению записей"""
    records_count = await rq.get_work_records_count()
    
    if records_count == 0:
        await callback.message.answer(
            "📭 В базе данных нет записей для удаления.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
                ]
            )
        )
        await callback.answer()
        return
    
    # Используем answer вместо edit_text
    await callback.message.answer(
        f"🗑️ *Удаление записей о работе*\n\n"
        f"В базе данных: *{records_count}* записей\n\n"
        f"*Рекомендуется сначала получить отчет,*\n"
        f"*а потом удалять записи.*\n\n"
        f"Что вы хотите сделать?",
        parse_mode="Markdown",
        reply_markup=kb.confirm_delete_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin_confirm_clear")
async def admin_confirm_clear(callback: CallbackQuery):
    """Удалить все записи о работе"""
    # Получаем количество записей до удаления
    records_before = await rq.get_work_records_count()
    
    if records_before == 0:
        await callback.message.answer(
            "📭 Нечего удалять - записей нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="admin_panel")]
                ]
            )
        )
        await callback.answer()
        return
    
    # Удаляем записи
    deleted_count = await rq.delete_all_work_records()
    
    # Используем answer вместо edit_text
    await callback.message.answer(
        f"✅ *Записи удалены!*\n\n"
        f"🗑️ Удалено записей: *{deleted_count}*\n"
        f"📊 Очищена таблица: *work_info*\n\n"
        f"*Данные сотрудников (ФИО, пароли) сохранены.*\n"
        f"Сотрудники могут продолжать работу.\n"
        f"Новые записи будут добавляться с чистого листа.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ В админ-панель", callback_data="admin_panel")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    records_count = await rq.get_work_records_count()
    
    if records_count == 0:
        await callback.message.answer(
            "📭 Статистика пуста - нет записей о работе.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
                ]
            )
        )
        await callback.answer()
        return
    
    # Получаем все записи для статистики
    records = await rq.get_all_work_with_users()
    
    # Считаем статистику
    total_hours = 0
    users_stats = {}
    
    for info, fullname in records:
        user_name = fullname or f"ID_{info.user_id}"
        
        if user_name not in users_stats:
            users_stats[user_name] = {
                'count': 0,
                'hours': 0,
                'user_id': info.user_id
            }
        
        users_stats[user_name]['count'] += 1
        try:
            hours = float(info.hours)
            users_stats[user_name]['hours'] += hours
            total_hours += hours
        except:
            pass
    
    # Формируем отчет
    stats_text = [
        f"📈 *СТАТИСТИКА РАБОТЫ*\n",
        f"📊 Всего записей: *{records_count}*",
        f"⏰ Всего часов: *{total_hours:.1f}*",
        f"👥 Участников: *{len(users_stats)}*",
        "=" * 30 + "\n",
        "*ТОП сотрудников:*\n"
    ]
    
    # Сортируем по количеству записей
    sorted_users = sorted(users_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for i, (user_name, stats) in enumerate(sorted_users[:5], 1):
        stats_text.append(
            f"{i}. *{user_name}*\n"
            f"   📋 {stats['count']} зап. | ⏰ {stats['hours']:.1f} ч."
        )
    
    stats_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Получить отчет", callback_data="admin_get_report"),
                InlineKeyboardButton(text="🗑️ Удалить записи", callback_data="admin_clear_records")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel1")
            ]
        ]
    )
    
    await callback.message.answer(
        "\n".join(stats_text),
        parse_mode="Markdown",
        reply_markup=stats_keyboard
    )
    await callback.answer()
    

@router.callback_query(F.data == "tasks")
async def tasks(callback: CallbackQuery): 
    await callback.message.answer("Это функция временно на доработке") 


# your_notes
@router.callback_query(F.data == "your_notes")
async def tasks(callback: CallbackQuery): 
    await callback.message.answer("Это функция временно на доработке") 


@router.callback_query(F.data == "admin_panel1")
async def back_panel1(callback: CallbackQuery):
    await callback.message.answer("Вернул вас назад в панель администратора, можете выбирать нужную функцию",
                                  reply_markup=kb.admin_menu)


@router.callback_query(F.data == "back_to_menu")
async def back_2_menu(callback: CallbackQuery):
    await callback.message.answer("Вернул вас назад в главное меню рабочей панели", 
                                  reply_markup=kb.personal_menu)
    

@router.callback_query(F.data == "last_info")
async def last_info(callback: CallbackQuery):
    await callback.message.answer("Вот ваша последняя запись, вы можете её изменить",
                                  reply_markup=kb.last_info_menu)


@router.callback_query(F.data == "back_info_menu")
async def back_2_info_menu(callback: CallbackQuery):
    await callback.message.answer("Вернул вас назад в меню записи о работе", 
                                  reply_markup=kb.info_menu)
