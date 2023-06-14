from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import logging
import random
from typing import List
from currency_converter import convert_currency_price_to_irr
import constants


logging.basicConfig(format='%(levelname)s - (%(asctime)s) - %(message)s - (Line: %(lineno)d) - [%(filename)s]',
                    filename='log.txt',
                    datefmt='%H:%M:%S',
                    encoding='utf-8',
                    level=logging.WARNING)

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s has stated the bot", update.effective_user.id)
    reply_keyboard=[
                ["Play Dice", "Play math quiz", "IRR exchange ratio"],
                ["About me", "Help"]    
                ]
    await context.bot.send_message(
        chat_id = update.message.chat.id,
        text= "Welcome to my Telegram Bot.\n"
        "You can see USD/IRR exchange ratio and also play two games including Dice and math quiz."
        "\n\n\nNote: This test bot has been deployed on PythonAnywere.com and unfortunately on this free server this bot can't get price from API!!!"
        "\nPlease deploy this bot localy to test exchange price notifier feature",
        reply_to_message_id= update.effective_message.id,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Choose one following",
        ),
    )

# Dice
async def dice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s wants to play Dice", update.effective_user.id)
    await context.bot.send_dice(
        chat_id= update.message.chat_id,
        reply_to_message_id= update.effective_message.id)

# Math quiz
START_ROUTES, END_ROUTES = range(2) ## Stages
FIRST_QUESTION, SECOND_QUESTION, THIRD_QUESTION = range(3) ## Callback data

def generate_question_and_return_answer(context: ContextTypes.DEFAULT_TYPE):
    context.user_data['rand_x'] = random.randint(0, 100)
    context.user_data['rand_y'] = random.randint(0, 100)
    return context.user_data['rand_x'] + context.user_data['rand_y']

def generate_user_keyboard(answer: int, state: int) -> List[List[InlineKeyboardButton]]:
    keyboard = [
        [
            InlineKeyboardButton(text=f"{answer - 2}",
                                 callback_data=f"{str(state)}_incorrect"),
            InlineKeyboardButton(text=f"{answer + 1}",
                                 callback_data=f"{str(state)}_incorrect")
        ],
        [
            InlineKeyboardButton(text=f"{answer}",
                                 callback_data=f"{str(state)}_correct"),
            InlineKeyboardButton(text=f"{answer + 10}",
                                 callback_data=f"{str(state)}_incorrect")
        ]
    ]
    random.shuffle(keyboard)
    return keyboard

async def quiz_starter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s started quiz conversation", update.effective_user.id)
    answer = generate_question_and_return_answer(context)
    keyboard = generate_user_keyboard(answer, FIRST_QUESTION)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Let's start with a math pop quiz.\n\n"
             f"1/3: What is {context.user_data['rand_x']} + {context.user_data['rand_y']} ?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    return START_ROUTES

async def first_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s entered first question", update.effective_user.id)
    query = update.callback_query
    await query.answer()
    answer = generate_question_and_return_answer(context)
    keyboard = generate_user_keyboard(answer, SECOND_QUESTION)
    await query.edit_message_text(
        text=f"Your answer was {query.data.split('_')[1]}.\n"
             "Your question is:\n\n"
             f"2/3: What's {context.user_data['rand_x']} + {context.user_data['rand_y']} ?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    return START_ROUTES

async def second_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s entered second question", update.effective_user.id)
    query = update.callback_query
    await query.answer()
    answer = generate_question_and_return_answer(context)
    keyboard = generate_user_keyboard(answer, THIRD_QUESTION)
    await query.edit_message_text(
        text=f"Your answer was {query.data.split('_')[1]}.\n"
             "Your question is:\n\n"
             f"3/3: What's {context.user_data['rand_x']} + {context.user_data['rand_y']} ?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    return START_ROUTES

async def third_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s entered third question", update.effective_user.id)
    query = update.callback_query
    await query.answer()
    text = f"Your answer was {query.data.split('_')[1]}." \
           f"Do you want to start over?"
    keyboard = [
        [InlineKeyboardButton(text="YES", callback_data="START_OVER")],
        [InlineKeyboardButton(text="NO!", callback_data="CANCEL")]
    ]
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    return END_ROUTES

async def start_over_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s start over quiz math", update.effective_user.id)
    query = update.callback_query
    await query.answer()
    answer = generate_question_and_return_answer(context)
    keyboard = generate_user_keyboard(answer, FIRST_QUESTION)
    await query.edit_message_text(
        text="Nice. Glad to have you.\n"
             "Let's start.\n\n"
             f"1/3: What is {context.user_data['rand_x']} + {context.user_data['rand_y']} ?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    return START_ROUTES

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s has ended the quiz conversation", update.effective_user.id)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Thank you for testing my bot!")
    return ConversationHandler.END

# Exchange section
async def exchange_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s wants to use exchange", update.effective_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You can use this section in the following manner:\n"
             "/set <int> -> send you a message of convert USD to IRR after <int> seconds\n\n"
             "/unset -> unset",
        reply_to_message_id=update.effective_message.id
    )

async def currency_alert_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    base = "USD"
    due = job.data["due"]
    price = convert_currency_price_to_irr(base, constants.ExURL, constants.ExAPI)
    resp = await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"Convert For {base} To IRR: {price}\n"
             f"I will notify you after {due} seconds!"
    )
    logger.warning(resp)

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE, base: str):
    all_jobs = context.job_queue.get_jobs_by_name(name)
    if not all_jobs:
        return False
    for job in all_jobs:
        if job.data["base"] == base:
            job.schedule_removal()
            logger.warning("job: %s (%s) has been removed", name, base)
    return True

async def set_currency_alert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        due = float(context.args[0])
        base = "USD"
        logger.warning("user %s set an exchange job for every %s seocnds and %s base currency", update.effective_user.id, str(due), base)
        job_name = str(update.effective_user.id)
        if due < 5:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please set an interval greater or equal than 5."
            )
            logger.warning("user %s set an exchange job wrongly, due is less than 5 seconds", update.effective_user.id)
            return
        job_removed = remove_job_if_exists(job_name, context, base)
        context.job_queue.run_repeating(
            currency_alert_job,
            chat_id=update.effective_chat.id,
            interval=due,
            name=job_name,
            data={
                "base": base,
                "due": due
            }
        )
        text = "Your requested job is created"
        logger.warning("user %s requested job is created", update.effective_user.id)
        
        if job_removed:
            text += "\nAll your jobs are deleted."
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text
        )
    except (IndexError, ValueError):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You used /set command wrongly!"
        )
        logger.warning("user %s has used /set command wrongly!", update.effective_user.id)

async def unset_alert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jobs = context.job_queue.get_jobs_by_name(str(update.effective_user.id))
        for job in jobs:
            if job.data["base"] == "USD":
                job.schedule_removal()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Your jobs are all deleted."
        )
        logger.warning("user %s unset the exchange notifier job", update.effective_user.id)

    except (IndexError, ValueError):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Your unset command is in wrong shape"
        )
        logger.warning("user %s couldn't unset the exchange notifier job", update.effective_user.id)

# Message Handlers
def generate_response(text: str) -> str:
    parsed_text = text.lower().strip()
    if "hello" in parsed_text or "hi" in parsed_text or "salam" in parsed_text:
        return "Hello to you"
    if "how are you" in parsed_text:
        return "I'm good thanks"
    if "xxx" in parsed_text:
        raise EOFError 
    return "Sorry, I can't understand you! Please ues /help"

async def response_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s wants to talk to me and has sent %s", update.effective_user.id, update.effective_message.text)
    chat_type = update.effective_chat.type
    
    if "About me" in update.effective_message.text:
        await aboutme_handler(update, context)
        return
    if "Play Dice" in update.effective_message.text:
        await dice_handler(update, context)
        return
    if "IRR exchange ratio" in update.effective_message.text:
        await exchange_help_handler(update, context)
        return
    if "Help" in update.effective_message.text:
        await help_handler(update, context)
        return

    if constants.BotUsername not in update.effective_message.text and chat_type == "group":
        return
    answer_text = generate_response(update.effective_message.text)
    user_first_name = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=answer_text + f"\n{user_first_name}",
        reply_to_message_id=update.effective_message.id
    )

# Help and Error    
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s wants help", update.effective_user.id)
    await context.bot.send_message(
        chat_id= update.message.chat_id,
        text="You shuold use buttons, Menu or following commands:\n /start \n /aboutme \n or use provided markup keyborad.",
        reply_to_message_id= update.effective_message.id)
    
async def aboutme_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning("user %s wants to know about me", update.effective_user.id)
    await context.bot.send_message(
        chat_id = update.message.chat_id,
        text= """
This bot is made for Quera Python LevelUp by MHBehroozi.\n
You can reach me:
On my Linkdin: www.linkedin.com/in/MHBehroozi/ \n
Or on my github: www.github.com/MHBehoozi/ \n
Or on my email address: hos.behroozi@gmail.com
        """,
        reply_to_message_id= update.effective_message.id
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"error: {context.error}")
    for dev_id in constants.DevID:
        await context.bot.send_message(
            chat_id=dev_id,
            text=f"ERROR!!!: {context.error} on update: {update}"
        )


# Main Section
if __name__ == '__main__':
    bot = ApplicationBuilder().token(constants.TOKEN).build()
    logger.critical('Robot has booted!')
    bot.add_handler(CommandHandler("start", start_handler))
    bot.add_handler(CommandHandler("aboutme", aboutme_handler))
    bot.add_handler(CommandHandler("dice", dice_handler))
    bot.add_handler(CommandHandler("help", help_handler))
    bot.add_handler(CommandHandler("exchange", exchange_help_handler))
    bot.add_handler(CommandHandler("set", set_currency_alert_handler))
    bot.add_handler(CommandHandler("unset", unset_alert_handler))
    conv_handler = ConversationHandler(
            entry_points=[CommandHandler("mathquiz", quiz_starter_handler),
                          MessageHandler(filters.Regex('Play math quiz'), quiz_starter_handler)],
            states={
                START_ROUTES: [
                    CallbackQueryHandler(first_question_handler, pattern=f"^{str(FIRST_QUESTION)}_.*$"),
                    CallbackQueryHandler(second_question_handler, pattern=f"^{str(SECOND_QUESTION)}_.*$"),
                    CallbackQueryHandler(third_question_handler, pattern=f"^{str(THIRD_QUESTION)}_.*$")
                ],
                END_ROUTES: [
                    CallbackQueryHandler(start_over_handler, pattern=f"^START_OVER$"),
                    CallbackQueryHandler(cancel_handler, pattern=f"^CANCEL$")
                ]
            },
            fallbacks=[],
            allow_reentry=True,
        )
    bot.add_handler(conv_handler)
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), response_to_message))
    bot.add_error_handler(error_handler)
    bot.run_polling(allowed_updates= ['TEXT', 'COMMAND'])
