from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import requests
from retrying import retry

app = Flask(__name__)
app.secret_key = 'default_secret_key'

API_URL = "https://tangerine-parsnip-y6waz72u9e7gr7id.salad.cloud/v1/chat/completions"
HEADERS = {
    'Content-Type': 'application/json'
}

login_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-form {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
        }
        .login-form h2 {
            margin-bottom: 20px;
        }
        .login-form input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .login-form button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            border: none;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <form action="/login" method="post" class="login-form">
            <h2>Login</h2>
            <input type="text" name="user_id" placeholder="User ID" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
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
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 600px;
            height: 100vh;
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
    </style>
</head>
<body>
    <div class="chat-container">
        <div id="chat-box" class="chat-box">
            <div class="message assistant">Hello! I am Clusty, an AI assistant developed by Cluster-Algopix. How can I help you today?</div>
        </div>
        <div id="input-box" class="input-box">
            <input type="text" id="user-input" placeholder="Type your message here...">
            <button onclick="sendMessage()">Send</button>
        </div>
        <div id="loading" class="loading" style="display:none;">
            <img src="https://i.imgur.com/PwFpbLL.gif" alt="Loading..." width="50" height="50">
        </div>
        <div class="logout-box">
            <a href="/logout">Logout</a>
        </div>
    </div>
    <script>
        async function sendMessage() {
            const userInput = document.getElementById('user-input').value;
            if (!userInput) return;

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
                    body: JSON.stringify({ message: userInput })
                });

                const data = await response.json();
                hideLoading();

                const assistantMessageDiv = document.createElement('div');
                assistantMessageDiv.classList.add('message', 'assistant');
                assistantMessageDiv.innerText = data.message;
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

@retry(stop_max_attempt_number=3, wait_fixed=10000)  # Retry 3 times with a 2-second interval
def get_ai_response(user_message):
    payload = {
        "model": "Jyotirmoy-Cluster/Clusty",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    
    try:
        assistant_message = get_ai_response(user_message)
        return jsonify({'message': assistant_message})
    except Exception as e:
        print(f"Error contacting AI model: {str(e)}")
        return jsonify({'message': 'Error: Could not contact the AI model.'}), 504

if __name__ == '__main__':
    app.run(debug=True)

