from aiogram import types
from aiogram.utils.chat_action import ChatActionSender
from random import randint

from hehbot.gpt import repo_conversation, GPT, ConversationMessage
from hehbot import *

allowed_chats = [-1002131963990, 788237639, -1001909232100, -1001568642353, -1001947307140]
command_said = False

user_message_times = {}

async def get_mentioned_user(msg: types.Message):
    if msg.reply_to_message:
        if msg.reply_to_message.from_user:
            if msg.reply_to_message.from_user.username and not msg.reply_to_message.from_user.is_bot:
                return f' (${msg.reply_to_message.from_user.username})'
    return ''

async def get_quoted_user(msg: types.Message):
    if msg.reply_to_message:
        if msg.reply_to_message.from_user:
            if msg.reply_to_message.from_user.username and not msg.reply_to_message.from_user.is_bot:
                return f'Цитую особу з іменем {msg.reply_to_message.from_user.full_name} і його текст виглядає так: "{msg.reply_to_message.text}"'

async def do_command(msg: types.Message) -> ChatMessage | None:
    # process user's text if has commands

    if BotCommand.count_commands(msg.text) == 1:
        cmd_result = await BotCommand.cmd_by_text(msg, msg.text + await get_mentioned_user(msg))
        if cmd_result:
            m = await ChatMessage.from_telegram(msg)
            m.text = cmd_result
            await repo_msg.add_message(m)
            return m
    return None


@dp.message()
async def handler_filter_message(msg: types.Message) -> None:

    
    # person create or update and get
    person = await verify_user(msg)
    if not person:
        return # person was notified
    
    #await msg.reply(await gpt.generate_text(msg))

    if str(msg.text).startswith('/'):
        cmd_msg = await do_command(msg)
        if cmd_msg:
            await msg.reply(cmd_msg.text)    
        return
    
    repo_user.delete(-2)

    
    # find command by AI and send if True
    cmd = await BotCommand.compare_async(msg.text) 

    if isinstance(cmd, bool):
        from hehbot.gpt import GPT
        await msg.reply(await GPT.answer(msg.chat.id, person.number, msg.text, quoted_user_and_text=await get_quoted_user(msg)))
    else:
        async with ChatActionSender.typing(msg.chat.id, bot):
            execution = await cmd.execute(msg, '', msg.text + await get_mentioned_user(msg))
            if execution:
                await msg.answer(execution)


async def verify_user(msg: types.Message) -> Person | None:

     # check if message is forwarded
    if msg.is_automatic_forward or msg.forward_from or msg.forward_from_message_id or msg.forward_origin:
        return None
    
    # check if message has text
    if not msg.text:
        return None
    
    # check if message is command
    if str(msg.text).lower().startswith('суд') or str(msg.text).startswith('/'):
        # message has text
        if len(str(msg.text)) > 200:
            await msg.reply("Я не читаю повідомлення в яких більше 200 літер.")
            return None
         
        # send instructions if msg chat is private
        elif msg.chat.type == 'private' and msg.text.startswith('/start'):
            from hehbot.command import detailed_info_command
            await detailed_info_command.execute(msg, '', msg.text)
            return None
    else:
        return None
    
    # chat id in whitelist
    if msg.chat.id not in allowed_chats:
        await msg.answer("Цей чат не зареєстрований в системі.")
        print(f'намагалися писати в чаті: {msg.chat.id}')
        return None

    # person: create or update
    person = await repo_user.update_by_telegram_async(msg)

    # person cannot be created or received
    if not person:
        await msg.answer("Ви не зареєстровані в системі. Я зареєструю самостійно, якщо у вашому профілі буде ім'я та нікнейм.")
        return None
    
    # check if user can send message
    if not await repo_msg.can_send_message(person.number, msg.chat.id, 2):
        await msg.reply('Не флуди, будь ласка.')
        return None
    
    if not msg.text.startswith('/bet'):
        await repo_msg.add_message(ChatMessage(msg.text, msg.date, msg.chat.id, person.id, person.number))
    
    return person