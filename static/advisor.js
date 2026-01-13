function toggleAIChat() {
    const chatWindow = document.getElementById('aiChatWindow');
    const toggleBtn = document.getElementById('aiToggleBtn');
    
    if (chatWindow.style.display === 'none' || !chatWindow.style.display) {
        chatWindow.style.display = 'block';
        toggleBtn.style.display = 'none';
        // Focus on input after animation
        setTimeout(() => {
            document.getElementById('aiMessageInput').focus();
        }, 100);
    } else {
        chatWindow.style.display = 'none';
        toggleBtn.style.display = 'flex';
    }
}

function sendAIMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById('aiMessageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to backend
    fetch('/api/ai-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator();
        addMessageToChat(data.response, 'bot');
    })
    .catch(error => {
        removeTypingIndicator();
        addMessageToChat('Sorry, I encountered an error processing your request. Please try again.', 'bot');
        console.error('AI Chat Error:', error);
    });
}

function addMessageToChat(message, sender) {
    const messagesContainer = document.getElementById('aiChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ai-message-${sender} mb-3`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start gap-2 justify-content-end">
                <div class="ai-message-content p-3">
                    <p class="mb-0">${escapeHtml(message)}</p>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start gap-2">
                <div class="ai-avatar d-flex align-items-center justify-content-center">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M17 8.5C17 5.5 14.5 3 11.5 3C11.5 3 11.5 6 11.5 8.5C11.5 11 14 13.5 17 13.5C17 13.5 17 11.5 17 8.5Z" fill="currentColor"/>
                    </svg>
                </div>
                <div class="ai-message-content p-3">
                    <p class="mb-0">${escapeHtml(message)}</p>
                </div>
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    // Smooth scroll to bottom
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('aiChatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'ai-message ai-message-bot mb-3';
    typingDiv.innerHTML = `
        <div class="d-flex align-items-start gap-2">
            <div class="ai-avatar d-flex align-items-center justify-content-center">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17 8.5C17 5.5 14.5 3 11.5 3C11.5 3 11.5 6 11.5 8.5C11.5 11 14 13.5 17 13.5C17 13.5 17 11.5 17 8.5Z" fill="currentColor"/>
                </svg>
            </div>
            <div class="ai-message-content p-3">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}