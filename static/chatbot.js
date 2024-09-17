function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    if (message.trim() === '') {
        return;
    }

    appendMessage('Você', message, 'user');

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pergunta: message }),
    })
    .then(response => response.json())
    .then(data => {
        appendMessage('Chatbot', data.resposta, 'bot');
        userInput.value = '';
    })
    .catch(error => {
        console.error('Erro:', error);
    });
}

function appendMessage(sender, message, className) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', className);
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;  // Rolagem automática para o final
}
