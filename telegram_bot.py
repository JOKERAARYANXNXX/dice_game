# telegram_bot.py
import redis
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from bot_config import TELEGRAM_BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

# Connect to Redis
r = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True
)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the Dice Challenge Bot! Use /challenge to challenge other players.')

def challenge(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    challenger = user.username
    challenge_message = f"{challenger} has challenged everyone! Who wants to accept?"

    keyboard = [[InlineKeyboardButton("Accept Challenge", callback_data=f'accept_{challenger}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(challenge_message, reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data.split('_')
    if data[0] == 'accept':
        challenger = data[1]
        acceptor = query.from_user.username
        game_result = play_game(challenger, acceptor)
        query.edit_message_text(text=game_result)

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
    result_message = (f"{challenger} vs {acceptor}\n"
                      f"{challenger}'s score: {challenger_score}\n"
                      f"{acceptor}'s score: {acceptor_score}\n"
                      f"Winner: {winner}!")

    return result_message

def update_leaderboard(winner: str, score: int) -> None:
    r.zincrby('leaderboard', score, winner)

def leaderboard(update: Update, context: CallbackContext) -> None:
    top_players = r.zrevrange('leaderboard', 0, 9, withscores=True)
    leaderboard_message = "🏆 Leaderboard 🏆\n\n"
    for rank, (player, score) in enumerate(top_players, start=1):
        leaderboard_message += f"{rank}. {player}: {int(score)}\n"

    update.message.reply_text(leaderboard_message)

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("challenge", challenge))
    dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
