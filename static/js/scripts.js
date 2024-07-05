async function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (!userInput) return;
    
    const chatBox = document.getElementById('chat-box');
    const userMessageDiv = document.createElement('div');
    userMessageDiv.classList.add('message', 'user');
    userMessageDiv.innerText = userInput;
    chatBox.appendChild(userMessageDiv);
    
    document.getElementById('user-input').value = '';
    
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    });
    
    const data = await response.json();
    const assistantMessageDiv = document.createElement('div');
    assistantMessageDiv.classList.add('message', 'assistant');
    assistantMessageDiv.innerText = data.message;
    chatBox.appendChild(assistantMessageDiv);
    
    chatBox.scrollTop = chatBox.scrollHeight;
}
