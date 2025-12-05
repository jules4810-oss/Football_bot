import os
import json
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from predictor import load_teams, predict_match

# load token
cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(cfg_path):
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.example.json')

with open(cfg_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

TOKEN = cfg.get('TELEGRAM_TOKEN') or ''
if not TOKEN or 'paste-your-bot-token' in TOKEN:
    print('WARNING: TELEGRAM_TOKEN not set in config.json. Add it before running the bot.')

teams, meta = load_teams()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salut! Envoie `/predict EquipeA vs EquipeB` — ex: `/predict Paris_SG vs Real_Madrid`.\n"
        "Utilise des underscores pour les noms avec espace (ou édite teams.json)."
    )

def parse_predict_command(text):
    m = re.search(r'([\w_ ]+)\s+vs\s+([\w_ ]+)', text, re.IGNORECASE)
    if not m:
        parts = text.split()
        if len(parts) >= 3 and parts[1].lower() == 'vs':
            return parts[0], parts[2]
        return None
    home = m.group(1).strip().replace(' ', '_')
    away = m.group(2).strip().replace(' ', '_')
    return home, away

async def predict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ''
    parsed = parse_predict_command(text)
    if not parsed:
        await update.message.reply_text('Format invalide. Ex: /predict Paris_SG vs Real_Madrid')
        return
    home, away = parsed
    res = predict_match(home, away, teams, meta, max_goals=6)
    mh = res['most_likely_score']
    out = res['outcome_probabilities']
    msg = f"Prédiction pour {home.replace('_',' ')} vs {away.replace('_',' ')}\n"
    msg += f"Score le plus probable: {mh['home_goals']} - {mh['away_goals']} (prob: {mh['probability']:.1%})\n"
    msg += f"Espérance de buts: {res['expected_goals']['home']:.2f} - {res['expected_goals']['away']:.2f}\n"
    msg += f"Prob. victoire domicile: {out['home_win']:.1%} | Nul: {out['draw']:.1%} | Victoire visiteur: {out['away_win']:.1%}\n"
    msg += "\nConseil: édite teams.json pour affiner les forces des équipes."
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Usage: /predict EquipeA vs EquipeB")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ''
    if 'vs' in text.lower():
        parsed = parse_predict_command(text)
        if parsed:
            home, away = parsed
            res = predict_match(home, away, teams, meta, max_goals=6)
            mh = res['most_likely_score']
            out = res['outcome_probabilities']
            msg = f"{home.replace('_',' ')} {mh['home_goals']} - {mh['away_goals']} {away.replace('_',' ')} | "
            msg += f"H:{res['expected_goals']['home']:.2f} A:{res['expected_goals']['away']:.2f} | "
            msg += f"P(H/D/A): {out['home_win']:.1%}/{out['draw']:.1%}/{out['away_win']:.1%}"
            await update.message.reply_text(msg)
            return
    await update.message.reply_text('Je ne comprends pas. Envoie `/predict EquipeA vs EquipeB`')

def main():
    if not TOKEN or 'paste-your-bot-token' in TOKEN:
        print('Bot token manquant ou par défaut — ajoute ton token dans config.json et relance.')
        return
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('predict', predict_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print('Bot démarré (polling)...')
    app.run_polling()

if __name__ == '__main__':
    main()
