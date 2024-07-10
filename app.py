from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import requests
from retrying import retry

app = Flask(__name__)
app.secret_key = 'default_secret_key'

API_URL = "https://salmon-ranch-npn2zalp31eq19zg.salad.cloud/v1/chat/completions"
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer API12345'
}

login_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            margin-top: 50px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row">
            <div class="col s12 m6 offset-m3">
                <div class="card">
                    <div class="card-content">
                        <span class="card-title">Login</span>
                        <form action="/login" method="post">
                            <div class="input-field">
                                <input type="text" name="user_id" id="user_id" required>
                                <label for="user_id">User ID</label>
                            </div>
                            <div class="input-field">
                                <input type="password" name="password" id="password" required>
                                <label for="password">Password</label>
                            </div>
                            <button type="submit" class="btn waves-effect waves-light">Login</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
</body>
</html>
"""

index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat with Clusty</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 600px;
            height: 80vh;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        .chat-box {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            word-wrap: break-word;
        }
        .user {
            background-color: #e0f7fa;
            text-align: right;
        }
        .assistant {
            background-color: #f1f8e9;
        }
        .input-box {
            display: flex;
            padding: 10px;
            border-top: 1px solid #ccc;
        }
        .input-box input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px 0 0 5px;
        }
        .input-box button {
            padding: 10px;
            background-color: #007bff;
            border: none;
            color: white;
            border-radius: 0 5px 5px 0;
            cursor: pointer;
        }
        .loading {
            text-align: center;
            padding: 10px;
        }
        .logout-box {
            padding: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div id="chat-box" class="chat-box">
            <div class="message assistant">Hello! I am Clusty, an AI assistant developed by Cluster-Algopix. How can I help you today?</div>
        </div>
        <div id="input-box" class="input-box">
            <input type="text" id="system-input" placeholder="Enter system message here...">
            <input type="text" id="user-input" placeholder="Type your message here...">
            <button onclick="sendMessage()">Send</button>
        </div>
        <div id="loading" class="loading" style="display:none;">
            <img src="https://i.imgur.com/PwFpbLL.gif" alt="Loading..." width="50" height="50">
        </div>
        <div class="logout-box">
            <a href="/logout" class="btn">Logout</a>
        </div>
    </div>
    <script>
        // Define your JavaScript functions here
        async function sendMessage() {
            const systemInput = document.getElementById('system-input').value;
            const userInput = document.getElementById('user-input').value;
            if (!systemInput || !userInput) return;

            const chatBox = document.getElementById('chat-box');
            const userMessageDiv = document.createElement('div');
            userMessageDiv.classList.add('message', 'user');
            userMessageDiv.innerText = userInput;
            chatBox.appendChild(userMessageDiv);

            document.getElementById('user-input').value = '';

            showLoading();

            try {
                const response = await fetchWithRetries('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ systemMessage: systemInput, userMessage: userInput })
                });

                const data = await response.json();
                hideLoading();

                const assistantMessageDiv = document.createElement('div');
                assistantMessageDiv.classList.add('message', 'assistant');
                assistantMessageDiv.innerHTML = formatResponse(data.message);
                chatBox.appendChild(assistantMessageDiv);

                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (error) {
                hideLoading();

                const errorMessageDiv = document.createElement('div');
                errorMessageDiv.classList.add('message', 'assistant');
                errorMessageDiv.innerText = 'Error: Could not contact the AI model.';
                chatBox.appendChild(errorMessageDiv);

                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        function formatResponse(response) {
            return response.replace(/\* /g, '<li>').replace(/Bullet Points: <br>/g, 'Bullet Points: <ul>') + '</ul>';
        }

        async function fetchWithRetries(url, options, retries = 3) {
            let attempt = 0;
            while (attempt < retries) {
                try {
                    const response = await fetch(url, options);
                    if (response.ok) {
                        return response;
                    }
                } catch (error) {
                    console.error('Fetch failed, retrying...', error);
                }
                attempt++;
            }
            throw new Error('Max retries exceeded');
        }

        function showLoading() {
            document.getElementById('loading').style.display = 'block';
        }

        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def login():
    return render_template_string(login_html)

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
    return render_template_string(index_html)

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_ai_response(system_message, user_message):
    payload = {
        "model": "Clusty",
        "messages": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0.5,
        "top_p": 1.0,
        "min_new_tokens": 1
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    system_message = data['systemMessage']
    user_message = data['userMessage']

    try:
        ai_response = get_ai_response(system_message, user_message)
        assistant_message = ai_response['choices'][0]['message']['content']
        return jsonify(message=assistant_message)
    except Exception as e:
        return jsonify(message=f"Error: Could not contact the AI model. {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
