from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Войти", callback_data="login")],
                                                   [InlineKeyboardButton(text="Регистрация", callback_data="registration")],
                                                   [InlineKeyboardButton(text="Админ панель", callback_data="admin_panel")]])


personal_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отчёты о работе", callback_data="work_info")],
                                                      [InlineKeyboardButton(text="Ваши заметки", callback_data="your_notes")],
                                                      [InlineKeyboardButton(text="Настройки", callback_data="profile")]])


info_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Записать информацию", callback_data="insert_info")],
                                                  [InlineKeyboardButton(text="Последняя запись", callback_data="last_info")],
                                                  [InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")]])


last_info_menu = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_info"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_info")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_info_menu")
        ]
    ]
)

profile_settings = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Ваша последняя запись", callback_data="last_info")],
                                                         [InlineKeyboardButton(text="Изменить ФИО", callback_data="change_fio")],
                                                         [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]])

# Кнопка отмены во время заполнения информации
cancel_button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_info")]])


admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Получить отчет", callback_data="admin_get_report"),
            InlineKeyboardButton(text="👥 Список сотрудников", callback_data="admin_users_list")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить записи", callback_data="admin_clear_records"),
            InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats")
        ],
    ]
)

# Клавиатура подтверждения удаления
confirm_delete_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ ДА, удалить", callback_data="admin_confirm_clear"),
            InlineKeyboardButton(text="📊 Сначала отчет", callback_data="admin_get_report")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel1")
        ]
    ]
)

# Клавиатура после отчета
after_report_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Удалить записи", callback_data="admin_clear_after_report"),
            InlineKeyboardButton(text="◀️ В меню", callback_data="admin_panel1")
        ]
    ]
)









































































































