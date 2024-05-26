# telegram_bot.py
import redis
import random
import time
import psutil
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from bot_config import TELEGRAM_BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Connect to Redis
r = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True
)

# Utility function to update bot stats
def update_bot_stats(stat_type: str, value: int = 1):
    r.hincrby('bot_stats', stat_type, value)

# Start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the Dice Challenge Bot! Use /challenge to challenge other players.')

# Ping command
def ping(update: Update, context: CallbackContext) -> None:
    start_time = time.time()
    update.message.reply_text('Pong!')
    end_time = time.time()
    response_time = int((end_time - start_time) * 1000)  # Convert to milliseconds
    update.message.reply_text(f'Pong! Response time: {response_time} ms')

# Challenge command
def challenge(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    challenger = user.username
    challenge_message = f"{challenger} has challenged everyone! Who wants to accept?"

    keyboard = [[InlineKeyboardButton("Accept Challenge", callback_data=f'accept_{challenger}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(challenge_message, reply_markup=reply_markup)
    update_bot_stats('total_games')

# Button callback
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    logger.info(f'Received callback query: {query.data}')

    data = query.data.split('_')
    if len(data) != 2 or data[0] != 'accept':
        logger.error(f'Invalid callback data: {query.data}')
        return

    challenger = data[1]
    acceptor = query.from_user.username

    logger.info(f'Challenger: {challenger}, Acceptor: {acceptor}')

    if challenger == acceptor:
        query.message.reply_text("You cannot accept your own challenge!")
        return

    game_result = play_game(challenger, acceptor)
    query.edit_message_text(text=game_result, parse_mode=ParseMode.MARKDOWN)
    update_bot_stats('games_played')

# Play game logic
def play_game(challenger: str, acceptor: str) -> str:
    challenger_score = sum(random.randint(1, 6) for _ in range(3))
    acceptor_score = sum(random.randint(1, 6) for _ in range(3))

    if challenger_score > acceptor_score:
        winner = challenger
        winner_score = challenger_score
    else:
        winner = acceptor
        winner_score = acceptor_score

    update_leaderboard(winner, winner_score)
    result_message = (f"*{challenger}* vs *{acceptor}*\n"
                      f"*{challenger}'s* score: {challenger_score}\n"
                      f"*{acceptor}'s* score: {acceptor_score}\n"
                      f"**Winner: {winner}**!")

    return result_message

# Update leaderboard
def update_leaderboard(winner: str, score: int) -> None:
    r.zincrby('leaderboard', score, winner)
    update_bot_stats('users', 1)

# Leaderboard command
def leaderboard(update: Update, context: CallbackContext) -> None:
    top_players = r.zrevrange('leaderboard', 0, 9, withscores=True)
    leaderboard_message = "🏆 *Leaderboard* 🏆\n\n"
    for rank, (player, score) in enumerate(top_players, start=1):
        leaderboard_message += f"{rank}. {player}: {int(score)}\n"

    update.message.reply_text(leaderboard_message, parse_mode=ParseMode.MARKDOWN)

# Server status command
# Server status command
def server_status(update: Update, context: CallbackContext) -> None:
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    server_message = (f"*Server Status:*\n"
                      f"CPU Usage: {cpu_usage}%\n"
                      f"Memory Usage: {memory_info.percent}%\n"
                      f"Total Memory: {memory_info.total / (1024 ** 3):.2f} GB\n"
                      f"Used Memory: {memory_info.used / (1024 ** 3):.2f} GB\n"
                      f"Free Memory: {memory_info.free / (1024 ** 3):.2f} GB\n"
                      f"Disk Usage: {disk_usage.percent}%\n"
                      f"Total Disk Space: {disk_usage.total / (1024 ** 3):.2f} GB\n"
                      f"Used Disk Space: {disk_usage.used / (1024 ** 3):.2f} GB\n"
                      f"Free Disk Space: {disk_usage.free / (1024 ** 3):.2f} GB")

    update.message.reply_text(server_message, parse_mode=ParseMode.MARKDOWN)

# Bot status command
def bot_status(update: Update, context: CallbackContext) -> None:
    bot_stats = r.hgetall('bot_stats')
    total_games = bot_stats.get('total_games', 0)
    games_played = bot_stats.get('games_played', 0)
    total_users = bot_stats.get('users', 0)
    total_groups = len(r.smembers('groups'))

    bot_message = (f"*Bot Status:*\n"
                   f"Total Groups: {total_groups}\n"
                   f"Total Games Played: {total_games}\n"
                   f"Games Played: {games_played}\n"
                   f"Total Users: {total_users}")

    update.message.reply_text(bot_message, parse_mode=ParseMode.MARKDOWN)

# Track groups command
def track_groups(update: Update, context: CallbackContext) -> None:
    group_id = update.message.chat_id
    r.sadd('groups', group_id)

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("ping", ping))
    dispatcher.add_handler(CommandHandler("challenge", challenge))
    dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))
    dispatcher.add_handler(CommandHandler("server_status", server_status))
    dispatcher.add_handler(CommandHandler("bot_status", bot_status))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.groups, track_groups))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
