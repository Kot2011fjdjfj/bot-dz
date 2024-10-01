import logging
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
#список файлов
homework_file = 'homework.txt'
schedule_file = 'schedule.txt'
homework_dict = {}
schedule_dict = {}
#загрузка дз
def load_homework():
    if os.path.exists(homework_file):
        with open(homework_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(': ', 1)
                    if len(parts) == 2:
                        subject, homework = parts
                        homework_dict.setdefault(subject, []).append(homework)
#сохранение дз
def save_homework():
    with open(homework_file, 'w', encoding='utf-8') as file:
        for subject, assignments in homework_dict.items():
            for homework in assignments:
                file.write(f"{subject}: {homework}\n")
#загрузка инфы в файл расписания
def load_schedule():
    if os.path.exists(schedule_file):
        with open(schedule_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(': ', 1)
                    if len(parts) == 2:
                        subject, schedule = parts
                        schedule_dict.setdefault(subject, []).append(schedule)

def save_schedule():
    with open(schedule_file, 'w', encoding='utf-8') as file:
        for subject, schedule_times in schedule_dict.items():
            for schedule_time in schedule_times:
                file.write(f"{subject}: {schedule_time}\n")
#список предметов и их знаков
subject_emojis = {
    "Геометрия": "📐",
    "Алгебра": "🧮",
    "Литература": "📖",
    "Русский": "🇷🇺",
    "История": "🏺",
    "Обществознание": "🫂",
    "Фин.Грамотность": "💰",
    "Вероятность": "📊",
    "Музыка": "🎶",
    "Информатика": "💻",
    "Немецкий": "🇩🇪",
    "Англиский": "🇺🇸",
    "География": "🌍",
    "Биология": "🍃",
}
#обработчик отображения дз
async def send_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "📚 *Список домашних заданий:*\n\n" if homework_dict else 'Нет домашних заданий.'
    for subject, assignments in homework_dict.items():
        emoji = subject_emojis.get(subject, "📝")
        response += f"{emoji} *{subject}:*\n"
        for i, homework in enumerate(assignments, start=1):
            response += f"   > {i}. {homework}\n"
        response += "\n" + "-" * 30 + "\n\n"

    sent_message = await update.message.reply_text(response, parse_mode='Markdown')
    await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
#обработчик отображения расписания
async def send_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "🗓️ *Расписание:*\n\n" if schedule_dict else 'Нет расписания.'
    for subject, times in schedule_dict.items():
        response += f"📝 *{subject}:*\n"
        for i, schedule in enumerate(times, start=1):
            response += f"   > {i}. {schedule}\n"
        response += "\n" + "-" * 30 + "\n\n"
    await update.message.reply_text(response, parse_mode='Markdown')
#оброботчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Привет! Я бот для сбора домашних заданий и расписания.\n'
        'Используй команду /add для добавления заданий сразу списком (одна строка — одно задание).\n'
        'Команда /dz покажет все задания.\n'
        'Команда /raspisanie покажет текущее расписание.\n'
        'Команда /edit <предмет> <номер задания> <новое задание> для редактирования.\n'
        'Команда /delete <предмет> <номер задания> для удаления.\n'
        'Команда /add_schedule для добавления расписания сразу списком.\n'
        'Команда /delete_schedule <предмет> <номер> для удаления времени из расписания.'
    )
#оброботчик команды /add
async def add_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        message = update.message.text.split('\n')[1:]
        for line in message:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                subject, homework = parts
                homework_dict.setdefault(subject, []).append(homework)
        save_homework()
        await update.message.reply_text('Домашние задания добавлены!')
    else:
        await update.message.reply_text('Введите задания списком: каждая строка — новый предмет и задание.')
#оброботчик команды /add_schedule
async def add_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        message = update.message.text.split('\n')[1:]
        for line in message:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                subject, schedule_time = parts
                schedule_dict.setdefault(subject, []).append(schedule_time)
        save_schedule()
        await update.message.reply_text('Расписание добавлено!')
    else:
        await update.message.reply_text('Введите расписание списком: каждая строка — новый предмет и время.')
#оброботчик команды /edit
async def edit_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) >= 3:
        subject = context.args[0]
        try:
            index = int(context.args[1]) - 1
            new_homework = ' '.join(context.args[2:])
            if subject in homework_dict and 0 <= index < len(homework_dict[subject]):
                homework_dict[subject][index] = new_homework
                save_homework()
                await update.message.reply_text(f'Задание по *{subject}* обновлено!')
            else:
                await update.message.reply_text('Задание не найдено.')
        except ValueError:
            await update.message.reply_text('Номер задания должен быть числом.')
    else:
        await update.message.reply_text('Используйте формат: /edit <предмет> <номер задания> <новое задание>')
#оброботчик команды /delete
async def delete_homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 2:
        subject = context.args[0]
        try:
            index = int(context.args[1]) - 1
            if subject in homework_dict and 0 <= index < len(homework_dict[subject]):
                del homework_dict[subject][index]
                if not homework_dict[subject]:
                    del homework_dict[subject]
                save_homework()
                await update.message.reply_text(f'Задание по *{subject}* удалено!')
            else:
                await update.message.reply_text('Задание не найдено.')
        except ValueError:
            await update.message.reply_text('Номер задания должен быть числом.')
    else:
        await update.message.reply_text('Используйте формат: /delete <предмет> <номер задания>')
#оброботчик команды /delete_schedule
async def delete_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 2:
        subject = context.args[0]
        try:
            index = int(context.args[1]) - 1
            if subject in schedule_dict and 0 <= index < len(schedule_dict[subject]):
                del schedule_dict[subject][index]
                if not schedule_dict[subject]:
                    del schedule_dict[subject]
                save_schedule()
                await update.message.reply_text(f'Время для *{subject}* удалено!')
            else:
                await update.message.reply_text('Время не найдено.')
        except ValueError:
            await update.message.reply_text('Номер времени должен быть числом.')
    else:
        await update.message.reply_text('Используйте формат: /delete_schedule <предмет> <номер>')
#ну вы поняли
def clear_homework():
    global homework_dict
    homework_dict.clear()
    save_homework()
    logger.info("Все домашние задания очищены.")
#ну вы поняли
def clear_schedule():
    global schedule_dict
    schedule_dict.clear()
    save_schedule()
    logger.info("Все расписания очищены.")

#тут мы загружаем дз из файлов
def main() -> None:
    load_homework()
    load_schedule()
    application = ApplicationBuilder().token("7177177518:AAGCXFgxplOQlRck_5W0_Bnp9lu4be9PyrQ").build()
#список команд типо
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_homework))
    application.add_handler(CommandHandler("edit", edit_homework))
    application.add_handler(CommandHandler("delete", delete_homework))
    application.add_handler(CommandHandler("dz", send_homework))
    application.add_handler(CommandHandler("raspisanie", send_schedule))
    application.add_handler(CommandHandler("add_schedule", add_schedule))
    application.add_handler(CommandHandler("delete_schedule", delete_schedule))
    
    application.run_polling()
#запуск бота
if __name__ == '__main__':
    main()
