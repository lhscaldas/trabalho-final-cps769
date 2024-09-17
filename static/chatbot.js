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

    let avatarHtml = '';
    if (className === 'user') {
        avatarHtml = '<div class="avatar" style="background-color: #007BFF;"></div>';
    } else {
        avatarHtml = '<div class="avatar" style="background-color: #6c757d;"></div>';
    }

    messageElement.innerHTML = `
        ${avatarHtml}
        <div class="message-content">${message}</div>
    `;

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;  // Rolagem automática para o final
}
