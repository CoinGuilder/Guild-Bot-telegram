from __future__ import annotations

import asyncio
import json
import os
import random
from typing import TYPE_CHECKING

from captcha.image import ImageCaptcha
from dotenv import load_dotenv
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.util import quick_markup

if TYPE_CHECKING:
    from io import BytesIO

    from telebot.types import ChatJoinRequest, Message, User

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR") or "./.data"
TG_API_TOKEN = os.getenv("TG_API_TOKEN")
APPROVED_GROUPS = [
    int(markup) for markup in os.getenv("APPROVED_GROUPS", "").split(",")
]

bot = AsyncTeleBot(TG_API_TOKEN)

try:
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
except Exception as error:
    raise Exception(f"Error creating data directory: {error}")


async def send_verification(user: User, approval_chat_id: int):
    """Send a verification message to the user.

    Args:
        user (User): User to send the verification message to.
        approval_chat_id (int): The chat id to approve the user to.
    """
    captcha_text = "".join([chr(random.randint(65, 90)) for _ in range(6)])

    image: BytesIO = ImageCaptcha(width=280, height=90).generate(captcha_text)

    try:
        with open(f"{DATA_DIR}/{user.id}.json", "w") as file:
            json.dump({}, file)
    except FileExistsError:
        pass

    with open(f"{DATA_DIR}/{user.id}.json", "r") as file:
        data = json.load(file)

    message = await bot.send_photo(
        user.id,
        image,
        caption="Please reply to this message with the characters shown in the image.",
    )

    data = {
        "captcha": captcha_text,
        "message_id": message.id,
        "approval_chat_id": approval_chat_id,
    }

    with open(f"{DATA_DIR}/{user.id}.json", "w") as file:
        json.dump(data, file)


async def check_verification(message: Message):
    """Check if the verification message is correct.

    Args:
        message (Message): The message passed through the handler.
    """
    try:
        with open(f"{DATA_DIR}/{message.from_user.id}.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        return

    captcha = data["captcha"]
    message_id = data["message_id"]
    approval_chat_id = data["approval_chat_id"]

    if message.reply_to_message.id != message_id:
        return

    if message.text == captcha:
        os.remove(f"{DATA_DIR}/{message.from_user.id}.json")

        await bot.send_message(
            message.chat.id, "Verification successful!", reply_to_message_id=message_id
        )
        await bot.approve_chat_join_request(approval_chat_id, message.from_user.id)


def messege_check(message: Message) -> bool:
    """A function to check if the message is a valid.

    Args:
        message (Message): The messaged passed through the handler.

    Returns:
        bool: True if the message is valid, False otherwise.
    """
    return len(message.text) == 6 and message.reply_to_message


@bot.message_handler(func=messege_check)
async def message_handle(message: Message):
    await check_verification(message)


def join_request_check(join_request: ChatJoinRequest) -> bool:
    """A function to check if the join request is valid.

    Args:
        join_request (ChatJoinRequest): The join request passed through the handler.

    Returns:
        bool: True if the join request is valid, False otherwise.
    """
    if join_request.from_user.is_bot:
        return False

    if not APPROVED_GROUPS:
        return True

    return join_request.chat.id in APPROVED_GROUPS


@bot.chat_join_request_handler(func=join_request_check)
async def chat_join_request_handle(join_request: ChatJoinRequest):
    await send_verification(join_request.from_user, join_request.chat.id)


@bot.message_handler(commands=["start"])
async def start(message: Message):
    mock_message = """
Welcome to **GuildBot**. Below will be your newly assigned wallets to insert $CG And $CGT tokens for Staking and arbitraging.

Bal $CG, $CGT, `0.0ETH` ($0)\n`​​0x9645B2f4E7aC87CD5959CB60123E78B00adb06b1`

Bal $CG, $CGT, `0.0ETH` ($0)\n`0x4655C5460441C9B6Da5C05De3947C46049bdF5a2`

Bal $CG, $CGT, `0.0ETH` ($0)
`0x3116cA2D32B7AAe3691f0eEF7B76fDdb383EbE3c`
"""

    markup = quick_markup(
        {
            "Stake": {"callback_data": "null"},
            "Unstake": {"callback_data": "null"},
            "Guild Bot Stats": {"callback_data": "null"},
            "Revenue Stats": {"callback_data": "null"},
            "Token Balances": {"callback_data": "null"},
            "Buy CGT": {"callback_data": "null"},
            "Reclaim CGT": {"callback_data": "null"},
            "dAPP Stats": {"callback_data": "null"},
            "Twitter": {"url": "https://twitter.com"},
            "Website": {"url": "https://coinguilder.com/"},
            "Telegram": {"url": "https://t.me/coinguilder"},
        },
        row_width=2,
    )

    # make a grid of buttons thats 2 markup 1 for 4 rows and 3 markup 1 for 1 last row

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    markup.row(
        telebot.types.InlineKeyboardButton("Stake CG", callback_data="null"),
        telebot.types.InlineKeyboardButton("Unstake CG", callback_data="null"),
    )

    markup.row(
        telebot.types.InlineKeyboardButton("Buy CGT", callback_data="null"),
        telebot.types.InlineKeyboardButton("Reclaim CGT", callback_data="null"),
    )

    markup.row(
        telebot.types.InlineKeyboardButton("Token Balances", callback_data="null"),
    )

    markup.row(
        telebot.types.InlineKeyboardButton("Guild Bot Stats", callback_data="null"),
        telebot.types.InlineKeyboardButton("Revenue Stats", callback_data="null"),
        telebot.types.InlineKeyboardButton("dAPP Stats", callback_data="null"),
    )

    markup.row(
        telebot.types.InlineKeyboardButton("Twitter", url="https://twitter.com"),
        telebot.types.InlineKeyboardButton("Website", url="https://coinguilder.com/"),
        telebot.types.InlineKeyboardButton("Telegram", url="https://t.me/coinguilder"),
    )

    await bot.send_message(
        message.chat.id, mock_message, reply_markup=markup, parse_mode="Markdown"
    )


asyncio.run(bot.polling())
