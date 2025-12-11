import json
import telebot
from prediction import PredictModel

# Charger le token depuis config.json
with open('config.json', 'r') as f:
    cfg = json.load(f)

TOKEN = cfg.get('TELEGRAM_TOKEN', '').strip()
if not TOKEN:
    print('ERROR: TELEGRAM_TOKEN not set in config.json. Put your token there before running.')
    raise SystemExit(1)

bot = telebot.TeleBot(TOKEN)
model = PredictModel()

# Commande start/help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "Salut! Je suis ton bot de prédiction ⚽\n\n"
        "Commandes disponibles:\n"
        "/teams - lister les équipes disponibles\n"
        "/predict teamA teamB - prédire un match (ex: /predict France Brazil)\n"
        "/predict_proba teamA teamB - probabilités (victoire/nul/défaite)\n"
        "/example - exemple d'utilisation\n\n"
        "Astuce: mets ton TOKEN dans config.json si tu veux déployer."
    )
    bot.reply_to(message, text)

# Lister les équipes
@bot.message_handler(commands=['teams'])
def list_teams(message):
    teams = model.list_teams()
    bot.reply_to(message, "Équipes disponibles:\n" + "\n".join(teams))

# Exemple d'utilisation
@bot.message_handler(commands=['example'])
def example(message):
    bot.reply_to(message, "Exemple: /predict France Brazil\nExemple proba: /predict_proba France Brazil")

# Prédiction simple
@bot.message_handler(commands=['predict'])
def predict_cmd(message):
    args = message.text.split()[1:]
    if len(args) < 2:
        bot.reply_to(message, "Usage: /predict teamA teamB (ex: /predict France Brazil)")
        return
    team_a = args[0].capitalize()
    team_b = args[1].capitalize()
    result = model.predict_score(team_a, team_b, sims=2000)
    text = f"Prédiction entre {team_a} vs {team_b}:\n" \
           f"Score moyen: {result['avg_score_a']:.2f} - {result['avg_score_b']:.2f}\n" \
           f"Score le plus probable: {result['most_probable'][0]} - {result['most_probable'][1]}"
    bot.reply_to(message, text)

# Prédiction probabilités
@bot.message_handler(commands=['predict_proba'])
def predict_proba_cmd(message):
    args = message.text.split()[1:]
    if len(args) < 2:
        bot.reply_to(message, "Usage: /predict_proba teamA teamB (ex: /predict_proba France Brazil)")
        return
    team_a = args[0].capitalize()
    team_b = args[1].capitalize()
    proba = model.predict_proba(team_a, team_b, sims=4000)
    text = (
        f"Probabilités pour {team_a} vs {team_b}:\n"
        f"{team_a} victoire: {proba['p_win']*100:.1f}%\n"
        f"Nul: {proba['p_draw']*100:.1f}%\n"
        f"{team_b} victoire: {proba['p_loss']*100:.1f}%\n"
        f"Score moyen: {proba['avg_a']:.2f} - {proba['avg_b']:.2f}"
    )
    bot.reply_to(message, text)

# Lancer le bot
if __name__ == '__main__':
    print('Bot Telegram démarré. Polling...')
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
