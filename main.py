import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import database

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
database.init_db()

# 1. Створення опитування
@bot.message_handler(commands=['game'])
def create_game(message):
    text = message.text.replace('/game', '').strip()
    if not text:
        bot.reply_to(message, "Вкажіть текст події. Наприклад: `/game Гра у п'ятницю о 19:00`", parse_mode="Markdown")
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Буду", callback_data=f"vote_yes_{message.message_id}"),
        InlineKeyboardButton("❌ Не буду", callback_data=f"vote_no_{message.message_id}")
    )
    sent_msg = bot.send_message(message.chat.id, f"⚽ **ПОДІЯ:** {text}\n\n**Учасники:**\nЩе немає відповідей.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    action, choice_type, event_id = call.data.split('_')
    choice = "Прийде" if choice_type == "yes" else "Не прийде"
    user_name = call.from_user.first_name + (f" ({call.from_user.username})" if call.from_user.username else "")
    
    database.update_vote(event_id, call.from_user.id, user_name, choice)
    votes = database.get_votes(event_id)
    
    yes_list = [f"• {name} (ID: `{uid}`)" for name, uid, ch in votes if ch == "Прийде"]
    no_list = [f"• {name} (ID: `{uid}`)" for name, uid, ch in votes if ch == "Не прийде"]
    
    text = call.message.text.split("\n\n**Учасники:**")[0]
    text += f"\n\n**Учасники:**\n\n✅ **Йдуть ({len(yes_list)}):**\n" + ("\n".join(yes_list) if yes_list else "Нікого")
    text += f"\n\n❌ **Не йдуть ({len(no_list)}):**\n" + ("\n".join(no_list) if no_list else "Нікого")
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(call.id, f"Видали відгук: {choice}")

# 2. Внесення статистики: /addstat USER_ID ГОЛИ АСИСТИ
@bot.message_handler(commands=['addstat'])
def add_stat(message):
    try:
        _, user_id, goals, assists = message.text.split()
        database.add_player_stat(int(user_id), int(goals), int(assists))
        bot.reply_to(message, f"Статистику для ID {user_id} оновлено!")
    except:
        bot.reply_to(message, "Формат: `/addstat USER_ID ГОЛИ АСИСТИ`\nПриклад: `/addstat 12345678 2 1`", parse_mode="Markdown")

# Перегляд статистики та Коефіцієнта Корисності (КК)
# Формула КК = (Голи * 1.5 + Асисти * 1.0) / Ігри
@bot.message_handler(commands=['stats'])
def show_stats(message):
    stats = database.get_all_stats()
    if not stats:
        bot.reply_to(message, "Статистика порожня.")
        return
    res = "📊 **Статистика гравців:**\n\n"
    for uid, games, goals, assists in stats:
        kk = round((goals * 1.5 + assists * 1.0) / games, 2) if games > 0 else 0
        res += f"ID: `{uid}` | Ігор: {games} | Г: {goals} | А: {assists} | **КК: {kk}**\n"
    bot.reply_to(message, res, parse_mode="Markdown")

# 3. Розподіл гравців на 2 рівні команди за КК
@bot.message_handler(commands=['teams'])
def make_teams(message):
    # Приклад зчитування ID гравців через пробіл після команди: /teams ID1 ID2 ID3 ID4
    ids = message.text.split()[1:]
    if not ids:
        bot.reply_to(message, "Вкажіть ID гравців через пробіл. Приклад: `/teams 12345 67890 11223 44556`", parse_mode="Markdown")
        return
    
    all_stats = {str(uid): (goals*1.5 + assists)/games if games > 0 else 0 for uid, games, goals, assists in database.get_all_stats()}
    
    players = []
    for uid in ids:
        kk = all_stats.get(uid, 0.0)
        players.append((uid, kk))
    
    # Сортування за спаданням КК
    players.sort(key=lambda x: x[1], reverse=True)
    
    team_a, team_b = [], []
    sum_a, sum_b = 0, 0
    
    # Ждіт-алгоритм для балансу
    for uid, kk in players:
        if sum_a <= sum_b:
            team_a.append((uid, kk))
            sum_a += kk
        else:
            team_b.append((uid, kk))
            sum_b += kk
            
    res = "⚖️ **Розподіл на команди:**\n\n🟢 **Команда А:**\n"
    res += "\n".join([f"• ID: `{uid}` (КК: {kk})" for uid, kk in team_a])
    res += f"\n*Сумарний КК:* {round(sum_a, 2)}\n\n🔵 **Команда Б:**\n"
    res += "\n".join([f"• ID: `{uid}` (КК: {kk})" for uid, kk in team_b])
    res += f"\n*Сумарний КК:* {round(sum_b, 2)}"
    
    bot.reply_to(message, res, parse_mode="Markdown")

bot.infinity_polling()
