from flask import Flask, request, jsonify
from predictor import load_teams, predict_match

app = Flask(__name__)
teams, meta = load_teams()

@app.route('/predict')
def predict():
    home = request.args.get('home')
    away = request.args.get('away')
    if not home or not away:
        return jsonify({"error": "please provide 'home' and 'away' query parameters"}), 400
    res = predict_match(home, away, teams, meta, max_goals=6)
    return jsonify(res)

@app.route('/')
def index():
    return jsonify({"message": "Football Prediction Agent running. Use /predict?home=TEAM&away=TEAM"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
