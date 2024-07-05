from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = "https://tangerine-parsnip-y6waz72u9e7gr7id.salad.cloud/v1/chat/completions"
HEADERS = {
    'Content-Type': 'application/json'
}

@app.route('/')
def index():
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
    
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    data = response.json()
    assistant_message = data['choices'][0]['message']['content']
    
    return jsonify({'message': assistant_message})

if __name__ == '__main__':
    app.run(debug=True)
