from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Войти", callback_data="login")],
                                                   [InlineKeyboardButton(text="Регистрация", callback_data="registration")],
                                                   [InlineKeyboardButton(text="Админ панель", callback_data="admin_panel")]])


personal_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отчёты о работе", callback_data="work_info")],
                                                      [InlineKeyboardButton(text="Ваши заметки", callback_data="your_notes")],
                                                      [InlineKeyboardButton(text="Настройки", callback_data="profile")]])


info_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Записать информацию", callback_data="insert_info")],
                                                  [InlineKeyboardButton(text="Список организаций", callback_data="org_list")],
                                                  [InlineKeyboardButton(text="Последняя запись", callback_data="last_info")],
                                                  [InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")]])


new_org_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Записать организацию", callback_data="newOrga")],
                                                     [InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")]])

cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")]])


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
                                                         [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")],
                                                         [InlineKeyboardButton(text="Выход в панель админа", callback_data="back_to_admin_list")]])

# Кнопка отмены во время заполнения информации
cancel_button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_info")]])


admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Добавить организацию", callback_data="get_organization")
        ],
        [
            InlineKeyboardButton(text="📊 Получить отчет", callback_data="admin_get_report"),
            InlineKeyboardButton(text="👥 Список сотрудников", callback_data="admin_users_list")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить записи", callback_data="admin_clear_records"),
            InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats")
        ],
        [InlineKeyboardButton(text="Выход в меню сотрудника", callback_data="go_to_staff_panel")]
    ]
)

# Кнопка списка всех организаций
organization_list = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="📊 Список организаций", callback_data="orglist")],
                     [InlineKeyboardButton(text="Добавить организацию", callback_data="add_org")],
                     [InlineKeyboardButton(text="Изменить список", callback_data="edit_list")],
                     [InlineKeyboardButton(text="◀️ В меню", callback_data="admin_panel1")]
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

back_admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="get_organization")]
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


#UPD
#Заметки
notes_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать заметку", callback_data="create_note")],
        [InlineKeyboardButton(text="📋 Мои заметки", callback_data="view_notes")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ]
)


#UPD: Функция создания клавиатуры для конкретной заметки (редактировать, удалить, назад)
def get_note_keyboard(note_id):
    """Создать клавиатуру для конкретной заметки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_note_{note_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_note_{note_id}")
            ],
            [InlineKeyboardButton(text="◀️ Назад к заметкам", callback_data="view_notes")]
        ]
    )


#UPD: Функция создания динамической клавиатуры со списком всех заметок пользователя
def get_notes_list_keyboard(notes):
    """Создать клавиатуру со списком заметок"""
    keyboard = []
    for note in notes:
        # Обрезаем название, если оно длиннее 30 символов
        title_display = note.title[:30] + "..." if len(note.title) > 30 else note.title
        keyboard.append([
            InlineKeyboardButton(
                text=f"📄 {title_display}",
                callback_data=f"show_note_{note.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="your_notes")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


#UPD: Функция создания клавиатуры подтверждения удаления заметки
def get_confirm_delete_note_keyboard(note_id):
    """Клавиатура подтверждения удаления заметки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_note_{note_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="view_notes")
            ]
        ]
    )


#UPD: Клавиатура возврата в меню заметок
back_to_notes_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к заметкам", callback_data="your_notes")]
    ]
)







































































































