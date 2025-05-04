from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from calendar_uploader.uploader import upload_shifts
from shared.calendar_api import load_shifts_from_db
from datetime import datetime, timedelta
from shared.logger import logger
from shared.user_db import get_user_employee, save_user_employee, load_employees

def get_current_week():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday

def should_auto_upload():
    """Проверяет, нужно ли автоматически загружать смены"""
    current_week = get_current_week()
    next_week = current_week + timedelta(weeks=1)
    shifts = load_shifts_from_db()
    
    if not shifts:
        return False
    
    for shift in shifts:
        shift_date = datetime.strptime(shift['start_time'], '%Y-%m-%d %H:%M:%S')
        if shift_date.date() >= next_week.date():
            return True
    return False

def get_main_menu(user_name: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text=f"Ты: {user_name}", callback_data="noop", disabled=True)],
        [InlineKeyboardButton(text="С кем я на смене", callback_data="on_shift")],
        [InlineKeyboardButton(text="Сменить пользователя", callback_data="change_user")],
        [InlineKeyboardButton(text="Дополнительно", callback_data="additional_menu")]
    ])
    return keyboard

def get_additional_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Добавить смены вручную", callback_data="manual_upload")],
        [InlineKeyboardButton(text="Обновить таблицу смен", callback_data="refresh_shifts")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_employee_selection_menu() -> InlineKeyboardMarkup:
    employees = load_employees()
    keyboard = []
    for employee in employees:
        keyboard.append([InlineKeyboardButton(
            text=employee,
            callback_data=f"select_employee:{employee}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Да", callback_data="confirm_refresh")],
        [InlineKeyboardButton(text="Нет", callback_data="cancel_refresh")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_additional")]
    ])
    return keyboard

async def process_on_shift(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил информацию о текущих сменах")
    try:
        shifts = load_shifts_from_db()
        logger.debug(f"Загружено смен из БД: {len(shifts)}")
        
        today = datetime.now()
        today_shifts = []
        
        for shift in shifts:
            shift_date = datetime.strptime(shift['start_time'], '%Y-%m-%d %H:%M:%S')
            if shift_date.date() == today.date():
                today_shifts.append(shift['employee_name'])
                logger.debug(f"Найдена смена на сегодня: {shift['employee_name']}")
        
        current_user = get_user_employee(callback.from_user.id) or "Не выбран"
        logger.debug(f"Текущий пользователь: {current_user}")
        
        if today_shifts:
            message = "Сегодня на смене:\n" + "\n".join(today_shifts)
        else:
            message = "Сегодня нет смен или информация не загружена."
            logger.info("На сегодня смен не найдено")
        
        new_text = f"{message}\n\nТекущий пользователь: {current_user}"
        
        if callback.message.text != new_text:
            await callback.message.edit_text(
                new_text,
                reply_markup=get_main_menu(current_user)
            )
            logger.debug("Сообщение обновлено")
        else:
            logger.debug("Сообщение не требует обновления")
            
        await callback.answer("Информация обновлена")
    except Exception as e:
        logger.error(f"Ошибка при проверке смен для пользователя {callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка, попробуйте еще раз")

async def cmd_start(message: types.Message):
    logger.info(f"Новая команда /start от пользователя {message.from_user.id}")
    user_id = message.from_user.id
    saved_employee = get_user_employee(user_id)
    
    if saved_employee:
        logger.info(f"Найден сохраненный сотрудник для {user_id}: {saved_employee}")
        await message.answer(
            f"С возвращением, {saved_employee}!\nЧто ты хочешь сделать?",
            reply_markup=get_main_menu(saved_employee)
        )
    else:
        logger.info(f"Новый пользователь {user_id}, запрашиваю выбор сотрудника")
        await message.answer(
            "Привет! Выбери кто ты из списка:",
            reply_markup=get_employee_selection_menu()
        )

async def process_employee_selection(callback: types.CallbackQuery):
    logger.info(f"Обработка выбора сотрудника от пользователя {callback.from_user.id}")
    try:
        if callback.data.startswith("select_employee:"):
            employee = callback.data.split(":", 1)[1]
            logger.debug(f"Выбран сотрудник: {employee}")
            
            if save_user_employee(callback.from_user.id, employee):
                logger.info(f"Пользователь {callback.from_user.id} сохранен как {employee}")
            else:
                logger.error(f"Ошибка при сохранении выбора сотрудника для {callback.from_user.id}")
            
            await callback.message.edit_text(
                f"Привет, {employee}!\nЧто ты хочешь сделать?",
                reply_markup=get_main_menu(employee)
            )
        elif callback.data == "change_user":
            logger.info(f"Пользователь {callback.from_user.id} запросил смену сотрудника")
            await callback.message.edit_text(
                "Выбери кто ты из списка:",
                reply_markup=get_employee_selection_menu()
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при выборе сотрудника {callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка, попробуйте еще раз")

async def process_manual_upload(callback: types.CallbackQuery):
    logger.info(f"Запрос ручной загрузки смен от пользователя {callback.from_user.id}")
    try:
        upload_shifts(force=True)
        logger.info("Ручная загрузка смен выполнена успешно")
        await callback.answer("Смены загружены в календарь")
    except Exception as e:
        logger.error(f"Ошибка при ручной загрузке смен: {e}")
        await callback.answer("Ошибка при загрузке смен")

async def refresh_shifts(callback: types.CallbackQuery):
    logger.info(f"Запрос обновления таблицы смен от пользователя {callback.from_user.id}")
    await callback.message.edit_text(
        "Вы действительно хотите обновить таблицу смен?",
        reply_markup=get_confirmation_menu()
    )
    await callback.answer()

async def process_refresh_confirmation(callback: types.CallbackQuery):
    if callback.data == "confirm_refresh":
        logger.info(f"Подтверждено обновление смен пользователем {callback.from_user.id}")
        try:
            upload_shifts()
            logger.info("Обновление таблицы смен выполнено успешно")
            await callback.answer("Таблица смен обновлена и загружена в календарь")
        except Exception as e:
            logger.error(f"Ошибка при обновлении таблицы смен: {e}")
            await callback.answer("Ошибка при обновлении таблицы")
    elif callback.data == "cancel_refresh":
        logger.info(f"Отменено обновление смен пользователем {callback.from_user.id}")
        await callback.answer("Обновление отменено")
    
    current_user = get_user_employee(callback.from_user.id) or "Не выбран"
    await callback.message.edit_text(
        f"Дополнительные функции (пользователь: {current_user}):",
        reply_markup=get_additional_menu()
    )

async def process_additional_menu(callback: types.CallbackQuery):
    logger.info(f"Запрос дополнительного меню от пользователя {callback.from_user.id}")
    try:
        current_text = callback.message.text
        current_user = get_user_employee(callback.from_user.id) or "Не выбран"
        logger.debug(f"Текущий пользователь: {current_user}")
        
        await callback.message.edit_text(
            f"Дополнительные функции (пользователь: {current_user}):",
            reply_markup=get_additional_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при открытии дополнительного меню: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз")

async def process_back_to_main(callback: types.CallbackQuery):
    logger.info(f"Возврат в главное меню от пользователя {callback.from_user.id}")
    try:
        current_user = get_user_employee(callback.from_user.id) or "Не выбран"
        logger.debug(f"Текущий пользователь: {current_user}")
        
        await callback.message.edit_text(
            f"Привет, {current_user}!\nЧто ты хочешь сделать?",
            reply_markup=get_main_menu(current_user)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        await callback.answer("Произошла ошибка. Попробуйте еще раз")

def register_handlers(dp):
    logger.info("Регистрация обработчиков команд главного меню")
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(process_employee_selection, lambda c: c.data and c.data.startswith("select_employee:"))
    dp.callback_query.register(process_on_shift, lambda c: c.data == "on_shift")
    dp.callback_query.register(process_employee_selection, lambda c: c.data == "change_user")
    dp.callback_query.register(process_manual_upload, lambda c: c.data == "manual_upload")
    dp.callback_query.register(refresh_shifts, lambda c: c.data == "refresh_shifts")
    dp.callback_query.register(process_refresh_confirmation, lambda c: c.data in ["confirm_refresh", "cancel_refresh"])
    dp.callback_query.register(process_additional_menu, lambda c: c.data == "additional_menu")
    dp.callback_query.register(process_back_to_main, lambda c: c.data == "back_to_main")
    logger.info("Все обработчики команд зарегистрированы успешно")
