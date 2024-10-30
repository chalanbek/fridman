from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import re
from sc_client.models import ScLinkContentType, ScConstruction, ScLinkContent, ScTemplate
from sc_kpm.identifiers import CommonIdentifiers
from sc_kpm import ScKeynodes
from sc_kpm.utils import create_link, get_link_content_data, check_edge
from sc_kpm.utils.action_utils import execute_agent, get_action_answer
from sc_client.constants import sc_types
from sc_client.client import create_elements, connect, disconnect, template_search, get_links_by_content
from sc_kpm.sc_sets import ScStructure
import json

user_data = dict()
url = "ws://localhost:8090/ws_json"
connect(url)
# Define the command handler for /start
NAME, SURNAME, PATRONYMIC, CLASS, CITY, LEVEL = range(6)
TOPICS = ['Логика и теория множеств', 'Алгебра и арифметика', 'Геометрия', 'Комбинаторика','Вероятность и статистика', 'Математический анализ', 'Методы']

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
    await update.message.reply_text("Оцените свой уровень знаний от 0 до 7:")
    return LEVEL

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['level'] = update.message.text
    context.user_data['id'] = update.message.chat_id

    result = create_profile(context.user_data)
    if not result:
        await update.message.reply_text("Профиль с таким id пользователя уже существует!")
        return ConversationHandler.END
    
    # Формирование сообщения для отправки
    registration_info = (
        f"Регистрация завершена!\n"
        f"Имя: {context.user_data['name']}\n"
        f"Фамилия: {context.user_data['surname']}\n"
        f"Отчество: {context.user_data['patronymic']}\n"
        f"Класс: {context.user_data['class']}\n"
        f"Город: {context.user_data['city']}\n"
        f"Уровень знаний: {context.user_data['level']}"
    )
    
    # Отправка данных в Telegram (замените 'YOUR_CHAT_ID' на ID вашего чата)
    await context.bot.send_message(chat_id=update.message.chat_id, text=registration_info)
    
    await update.message.reply_text("Спасибо! Ваши данные успешно отправлены.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END

async def get_task_info(update: Update, context: ContextTypes.DEFAULT_TYPE, action, number=None) -> str:
    if number == None:
        task_number = find_task_number(update.message.text)
    else:
        task_number = number
        
    if task_number == None:
        if 'current_problem' in context.user_data:
            task_number = context.user_data['current_problem']
        else:
            await update.message.reply_text('Похоже, вы забыли указать номер задачи и ничего не решаете в данный момент')
            return
    construction = ScConstruction()  # Create link for example
    construction.create_link(sc_types.LINK_CONST, ScLinkContent(task_number, ScLinkContentType.STRING))
    arg1 = create_elements(construction)[0]
    if action == 'action_get_solution_answer':
        concept_tg_id_ = ScKeynodes.resolve('concept_tg_id', sc_types.NODE_CONST_CLASS)
        [links_with_tg_id] = get_links_by_content(update.message.chat_id)
        for id in links_with_tg_id:
            if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_tg_id_, id):
                kwargs = dict(
                    arguments={arg1: False, 
                            id: False},
                    concepts=["question", action],
                )
                break
        else:
            await update.message.reply_text('Вы еще не зарегистрированы! (напишише /register чтобы сдеать это)')
            return
    else:
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
    context.user_data['current_problem'] = task_number
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

async def get_problem_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_text = await get_task_info(update,context,action='action_get_solution_answer')
    await update.message.reply_text(f'Ответ задачи: {result_text}', parse_mode='html')

async def get_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    concept_tg_id_ = ScKeynodes.resolve('concept_tg_id', sc_types.NODE_CONST_CLASS)
    [links_with_tg_id] = get_links_by_content(update.message.chat_id)
    for id in links_with_tg_id:
        if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_tg_id_, id):
            arg1 = id
            break
    else:
        await update.message.reply_text('Вы еще не зарегистрированы! (напишише /register чтобы сдеать это)')
        return
    
    kwargs = dict(
        arguments={arg1: False},
        concepts=["question", 'action_get_user_profile'],
    )

    action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
    if not is_successfully:
        await update.message.reply_text('Что-то не так...')
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
    await update.message.reply_text(f'Ваш профиль: {result_text}', parse_mode='html')

async def get_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['current_direction'] = 0
    current_direction = context.user_data['current_direction']
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=text)] for text in TOPICS])
    message = await update.message.reply_text('Please choose:', reply_markup=reply_markup)
    context.user_data['bot_id'] = message.message_id

async def onButton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query.data not in ['Показать задачи', 'Показать теоремы', 'Назад', 'Вернуться в каталог']:
        if not query.data.isnumeric():
            [links] = get_links_by_content(query.data)
            nrel_main_idtf = ScKeynodes.resolve('nrel_main_idtf', sc_types.NODE_CONST_NOROLE)
            for link in links:
                template = ScTemplate()
                template.triple_with_relation(
                    sc_types.NODE_VAR >> '_topic',
                    sc_types.EDGE_D_COMMON_VAR,
                    link,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_main_idtf
                )
                links1 = template_search(template)
                if len(links1) == 1:
                    if not check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, ScKeynodes.resolve('concept_theorem', sc_types.NODE_CONST_CLASS), links1[0].get('_topic')):
                        context.user_data['current_topic'] = get_link_content_data(link)
                        topic_addr = links1[0].get('_topic')
                        break
            else:
                [links] = get_links_by_content(query.data)
                nrel_theorem_name = ScKeynodes.resolve('nrel_theorem_name', sc_types.NODE_CONST_NOROLE)
                for link in links:
                    template = ScTemplate()
                    template.triple_with_relation(
                        sc_types.NODE_VAR >> '_theorem',
                        sc_types.EDGE_D_COMMON_VAR,
                        link,
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_theorem_name
                    )
                    links1 = template_search(template)
                    if len(links1) == 1:
                        theorem_link_addr = link
                        break
                        
                
                kwargs = dict(
                arguments={link: False},
                concepts=["question", 'action_get_theorem_text'],
                )

                action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
                if not is_successfully:
                    await query.message.reply_text('Что-то не так...')
                result = get_action_answer(action)
                template = ScTemplate()
                template.triple(
                    result,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    (sc_types.LINK_VAR, 'link')
                )
                result = template_search(template)
                link = result[0].get('link')
                result = get_link_content_data(link)
                await query.message.reply_text(result)
            result = await call_AgentGetCatalog(topic_addr, query, context, 1)

        else:
            result_text = await get_task_info(update,context,action='action_get_problem_text', number=query.data)
            await query.message.reply_text(f'Условие задачи: {result_text}', parse_mode='html')

    elif query.data == 'Назад':
        if context.user_data['current_direction'] > 1:
            [links] = get_links_by_content(context.user_data['current_topic'])
            nrel_main_idtf = ScKeynodes.resolve('nrel_main_idtf', sc_types.NODE_CONST_NOROLE)
            for link in links:
                template = ScTemplate()
                template.triple_with_relation(
                    sc_types.NODE_VAR >> '_topic',
                    sc_types.EDGE_D_COMMON_VAR,
                    link,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_main_idtf
                )
                links1 = template_search(template)
                if len(links1) == 1:
                    topic_addr = links1[0].get('_topic')
                    break

            template = ScTemplate()
            nrel_subtopic = ScKeynodes.resolve('nrel_subtopic', sc_types.NODE_CONST_NOROLE)

            template.triple_with_relation(
                sc_types.NODE_VAR >> '_topic',
                sc_types.EDGE_D_COMMON_VAR,
                topic_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_subtopic
            )
            topics = template_search(template)

            if len(topics) != 1:
                await query.message.reply_text(f'Что-то не так...{len(topics)}')
                return
            else:
                upper_topic_addr = topics[0].get('_topic')
                template = ScTemplate()
                template.triple_with_relation(
                    upper_topic_addr,
                    sc_types.EDGE_D_COMMON_VAR,
                    sc_types.LINK_VAR >> '_link',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_main_idtf
                )
                links = template_search(template)
                link_addr = links[0].get('_link')
                context.user_data['current_topic'] = get_link_content_data(link_addr)

            result = await call_AgentGetCatalog(upper_topic_addr, query, context, -1)
        else:
            result = await call_AgentGetCatalog(None, query, context, 0, result=TOPICS)

    elif query.data in ['Показать задачи', 'Показать теоремы']:
        [links] = get_links_by_content(context.user_data['current_topic'])
        nrel_main_idtf = ScKeynodes.resolve('nrel_main_idtf', sc_types.NODE_CONST_NOROLE)
        for link in links:
            template = ScTemplate()
            template.triple_with_relation(
                sc_types.NODE_VAR >> '_topic',
                sc_types.EDGE_D_COMMON_VAR,
                link,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_main_idtf
            )
            links1 = template_search(template)
            if len(links1) == 1:
                topic_addr = links1[0].get('_topic')
                break
        result = await call_AgentGetCatalogProblemsorTheorems("action_get_catalog_problems" if query.data == 'Показать задачи' else "action_get_catalog_theorems", topic_addr, query, context)

    elif query.data == 'Вернуться в каталог':
        [links] = get_links_by_content(context.user_data['current_topic'])
        nrel_main_idtf = ScKeynodes.resolve('nrel_main_idtf', sc_types.NODE_CONST_NOROLE)
        for link in links:
            template = ScTemplate()
            template.triple_with_relation(
                sc_types.NODE_VAR >> '_topic',
                sc_types.EDGE_D_COMMON_VAR,
                link,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_main_idtf
            )
            links1 = template_search(template)
            if len(links1) == 1:
                topic_addr = links1[0].get('_topic')
                break
        
        #print(topic_addr)
        result = await call_AgentGetCatalog(topic_addr, query, context, 0)

async def call_AgentGetCatalog(topic_addr, query, context, i, result=None) -> bool:
    if result == None:
        kwargs = dict(
        arguments={topic_addr: False},
        concepts=["question", 'action_get_catalog'],
        )

        action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
        if not is_successfully:
            await query.message.reply_text('Что-то не так...')
            return False
        result = get_action_answer(action)
        template = ScTemplate()
        template.triple(
            result,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            (sc_types.LINK_VAR, 'link')
        )
        result = template_search(template)
        link = result[0].get('link')
        result = get_link_content_data(link)
        result = json.loads(result)['1']
        result.append('Показать задачи')
        result.append('Показать теоремы')
        result.append('Назад')
        '''for element in ['-', '.', ',']:
            result = list(map(lambda el: el.replace(element, ' '),result))'''
        #print(result)
    if 'bot_id' in context.user_data:
        if result != TOPICS:
            context.user_data['current_direction'] += i
        else:
            #del context.user_data['current_topic']
            context.user_data['current_direction'] = 0
        await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=context.user_data['bot_id'],
                text="Please choose:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=text)] for text in result])
            )
        return  True
    else:
        return False
    
async def call_AgentGetCatalogProblemsorTheorems(agent, topic_addr, query, context):
    kwargs = dict(
    arguments={topic_addr: False},
    concepts=["question", agent],
    )

    action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
    if not is_successfully:
        await query.message.reply_text('Что-то не так...')
        return False
    result = get_action_answer(action)
    template = ScTemplate()
    template.triple(
        result,
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        (sc_types.LINK_VAR, 'link')
    )
    result = template_search(template)
    link = result[0].get('link')
    result = get_link_content_data(link)
    result = json.loads(result)['1']
    result.append('Вернуться в каталог')
    if 'bot_id' in context.user_data:
        await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=context.user_data['bot_id'],
                text="Please choose:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=text)] for text in result])
            )
        return  True
    else:
        return False
    
async def check_user_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    concept_tg_id_ = ScKeynodes.resolve('concept_tg_id', sc_types.NODE_CONST_CLASS)
    [links_with_tg_id] = get_links_by_content(update.message.chat_id)
    for id in links_with_tg_id:
        if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_tg_id_, id):
            template = ScTemplate()
            template.triple_with_relation(
                    (sc_types.NODE_VAR, 'user'),
                    sc_types.EDGE_D_COMMON_VAR,
                    id,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    ScKeynodes.resolve('nrel_tg_id', sc_types.NODE_CONST_NOROLE),
                )
            results = template_search(template)
            result_search = results[0]
            user_addr = result_search.get('user')
            break
    else:
        await update.message.reply_text('Вы еще не зарегистрированы! (напишите /register чтобы сделать это)')
        return
    
    construction = ScConstruction()  # Create link for example
    construction.create_link(sc_types.LINK_CONST, ScLinkContent(context.user_data['current_problem'], ScLinkContentType.STRING))
    construction.create_link(sc_types.LINK_CONST, ScLinkContent(re.sub("/answer\s*", "", update.message.text), ScLinkContentType.STRING))
    [arg1, arg2] = create_elements(construction)
    
    kwargs = dict(
        arguments={arg1: False,
                   arg2: False,
                   user_addr: False},
        concepts=["question", 'action_check_problem_solution_answer'],
    )

    action, is_successfully = execute_agent(**kwargs, wait_time=3)  # ScAddr(...), bool
    await update.message.reply_text(f'Правильно', parse_mode='html') if is_successfully else await update.message.reply_text(f'Неправильно', parse_mode='html')
    
def find_task_number(message):
    # Регулярное выражение для поиска номера задачи
    match = re.search(r'задач[уи]\s*(\d+)', message)
    
    if match:
        return match.group(1)  # Возвращаем номер задачи
    return None  # Если номер не найден, возвращаем None

def create_profile(user_data):
    construction = ScConstruction()  # Create link for example
    data_index = ['surname', 'name', 'patronymic', 'class', 'city', 'id', 'level']
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
            LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, level)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(MessageHandler(filters.Regex('как решать задачу'), get_hint))
    application.add_handler(MessageHandler(filters.Regex('краткое решение задачи'), get_short_solution))
    application.add_handler(MessageHandler(filters.Regex('полное решение задачи'), get_complete_solution))
    application.add_handler(MessageHandler(filters.Regex('условие задачи'), get_problem_text))
    application.add_handler(MessageHandler(filters.Regex('решать задачу'), get_problem_text))
    application.add_handler(MessageHandler(filters.Regex('ответ задачи'), get_problem_answer))
    application.add_handler(CommandHandler('answer', check_user_answer))

    application.add_handler(CommandHandler('profile', get_user_profile))
    application.add_handler(CommandHandler('catalog', get_catalog))
    application.add_handler(CallbackQueryHandler(onButton))
    application.add_handler(conv_handler)

    # Run the bot until you send a signal with Ctrl-C
    application.run_polling()

    disconnect()