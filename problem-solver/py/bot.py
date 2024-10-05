from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re
from sc_client.models import ScLinkContentType, ScConstruction, ScLinkContent, ScTemplate
from sc_kpm.identifiers import CommonIdentifiers
from sc_kpm.utils import create_link, get_link_content_data
from sc_kpm.utils.action_utils import execute_agent, get_action_answer
from sc_client.constants import sc_types
from sc_client.client import create_elements, connect, disconnect, template_search
from sc_kpm.sc_sets import ScStructure

url = "ws://localhost:8090/ws_json"
connect(url)
# Define the command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Стартовый текст")

# Define a message handler that echoes messages
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text.startswith('как решать задачу'):
        task_number = find_task_number(update.message.text)
        construction = ScConstruction()  # Create link for example
        construction.create_link(sc_types.LINK_CONST, ScLinkContent(task_number, ScLinkContentType.STRING))
        arg1 = create_elements(construction)[0]

        kwargs = dict(
            arguments={arg1: False},
            concepts=["question", "action_get_hint"],
        )

        action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
        print(action, is_successfully)
        result = get_action_answer(action)
        template = ScTemplate()
        template.triple(
            result,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            (sc_types.LINK_VAR, 'link')
        )
        result = template_search(template)
        if len(result) == 0:
            await update.message.reply_text('Нет такой задачи')
            return
        link = result[0].get('link')
        print(link)
        result_text = get_link_content_data(link)
        print(result_text)
        await update.message.reply_text(f'Подсказка: {result_text}')
    else:
        await update.message.reply_text(f'Как скажешь')

def find_task_number(message):
    # Регулярное выражение для поиска номера задачи
    match = re.search(r'задачу\s*(\d+)', message)
    
    if match:
        return match.group(1)  # Возвращаем номер задачи
    return None  # Если номер не найден, возвращаем None

if __name__ == "__main__":
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token("7766139967:AAEL6O8FYVTkSMNeaRdb1sDzemXW4r40SrA").build()

    # Add command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Add message handler for echoing messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    # Run the bot until you send a signal with Ctrl-C
    application.run_polling()

    disconnect()