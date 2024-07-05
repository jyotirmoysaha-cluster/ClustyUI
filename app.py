from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

API_URL = "https://tangerine-parsnip-y6waz72u9e7gr7id.salad.cloud/v1/chat/completions"
HEADERS = {
    'Content-Type': 'application/json'
}

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    user_id = request.form['user_id']
    password = request.form['password']
    if user_id == 'Cluster' and password == '123':
        session['logged_in'] = True
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    payload = {
        "model": "Jyotirmoy-Cluster/Clusty",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "max_tokens": 128
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        assistant_message = data['choices'][0]['message']['content']
        return jsonify({'message': assistant_message})
    except requests.exceptions.RequestException as e:
        return jsonify({'message': 'Error: Could not contact the AI model.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
