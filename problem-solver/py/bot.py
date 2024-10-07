from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import re
from sc_client.models import ScLinkContentType, ScConstruction, ScLinkContent, ScTemplate
from sc_kpm.identifiers import CommonIdentifiers
from sc_kpm.utils import create_link, get_link_content_data
from sc_kpm.utils.action_utils import execute_agent, get_action_answer
from sc_client.constants import sc_types
from sc_client.client import create_elements, connect, disconnect, template_search
from sc_kpm.sc_sets import ScStructure

user_data = dict()
url = "ws://localhost:8090/ws_json"
connect(url)
# Define the command handler for /start
NAME, SURNAME, PATRONYMIC, CLASS, CITY = range(5)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите ваше имя:")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите вашу фамилию:")
    return SURNAME

async def surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['surname'] = update.message.text
    await update.message.reply_text("Введите ваше отчество:")
    return PATRONYMIC

async def patronymic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['patronymic'] = update.message.text
    await update.message.reply_text("Введите ваш класс:")
    return CLASS

async def student_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['class'] = update.message.text
    await update.message.reply_text("Введите ваш город:")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['city'] = update.message.text
    context.user_data['id'] = update.message.chat_id

    result = create_profile(context.user_data)
    if not result:
        await update.message.reply_text("Что-то не так.")
        return ConversationHandler.END
    
    # Формирование сообщения для отправки
    registration_info = (
        f"Регистрация завершена!\n"
        f"Имя: {context.user_data['name']}\n"
        f"Фамилия: {context.user_data['surname']}\n"
        f"Отчество: {context.user_data['patronymic']}\n"
        f"Класс: {context.user_data['class']}\n"
        f"Город: {context.user_data['city']}"
    )
    
    # Отправка данных в Telegram (замените 'YOUR_CHAT_ID' на ID вашего чата)
    await context.bot.send_message(chat_id=update.message.chat_id, text=registration_info)
    
    await update.message.reply_text("Спасибо! Ваши данные успешно отправлены.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END

'''async def get_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_number = find_task_number(update.message.text)
    construction = ScConstruction()  # Create link for example
    construction.create_link(sc_types.LINK_CONST, ScLinkContent(task_number, ScLinkContentType.STRING))
    arg1 = create_elements(construction)[0]

    kwargs = dict(
        arguments={arg1: False},
        concepts=["question", "action_get_hint"],
    )

    action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
    if not is_successfully:
        await update.message.reply_text('Нет такой задачи')
        return
    result = get_action_answer(action)
    template = ScTemplate()
    template.triple(
        result,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        (sc_types.LINK_VAR, 'link')
    )
    result = template_search(template)
    link = result[0].get('link')
    result_text = get_link_content_data(link)
    await update.message.reply_text(result_text, parse_mode='html')'''

async def get_task_info(update: Update, context: ContextTypes.DEFAULT_TYPE, action) -> str:
    task_number = find_task_number(update.message.text)
    construction = ScConstruction()  # Create link for example
    construction.create_link(sc_types.LINK_CONST, ScLinkContent(task_number, ScLinkContentType.STRING))
    arg1 = create_elements(construction)[0]

    kwargs = dict(
        arguments={arg1: False},
        concepts=["question", action],
    )

    action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
    if not is_successfully:
        await update.message.reply_text('Нет такой задачи')
        return
    result = get_action_answer(action)
    template = ScTemplate()
    template.triple(
        result,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        (sc_types.LINK_VAR, 'link')
    )
    result = template_search(template)
    link = result[0].get('link')
    result_text = get_link_content_data(link)
    return result_text

async def get_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_text = await get_task_info(update,context,action='action_get_hint')
    await update.message.reply_text(f'Подсказка: {result_text}', parse_mode='html')
    
async def get_short_solution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_text = await get_task_info(update,context,action='action_get_short_solution')
    await update.message.reply_text(f'Краткое решение: {result_text}', parse_mode='html')

async def get_complete_solution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_text = await get_task_info(update,context,action='action_get_complete_solution')
    await update.message.reply_text(f'Полное решение: {result_text}', parse_mode='html')

async def get_problem_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_text = await get_task_info(update,context,action='action_get_problem_text')
    await update.message.reply_text(f'Условие задачи: {result_text}', parse_mode='html')

def find_task_number(message):
    # Регулярное выражение для поиска номера задачи
    match = re.search(r'задач[уи]\s*(\d+)', message)
    
    if match:
        return match.group(1)  # Возвращаем номер задачи
    return None  # Если номер не найден, возвращаем None

def create_profile(user_data):
    construction = ScConstruction()  # Create link for example
    data_index = ['surname', 'name', 'patronymic', 'class', 'city', 'id']
    for element in data_index:
        construction.create_link(sc_types.LINK_CONST, ScLinkContent(user_data[element], ScLinkContentType.STRING))
    args = create_elements(construction)

    kwargs = dict(
        arguments={arg: False for arg in args},
        concepts=["question", "action_create_user_profile"],
    )

    action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
    return is_successfully
    
if __name__ == "__main__":
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token("7766139967:AAEL6O8FYVTkSMNeaRdb1sDzemXW4r40SrA").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, surname)],
            PATRONYMIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, patronymic)],
            CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_class)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(MessageHandler(filters.Regex('как решать задачу'), get_hint))
    application.add_handler(MessageHandler(filters.Regex('краткое решение задачи'), get_short_solution))
    application.add_handler(MessageHandler(filters.Regex('полное решение задачи'), get_complete_solution))
    application.add_handler(MessageHandler(filters.Regex('условие задачи'), get_problem_text))

    application.add_handler(conv_handler)

    # Run the bot until you send a signal with Ctrl-C
    application.run_polling()

    disconnect()