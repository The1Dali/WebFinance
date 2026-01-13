// Voice Recognition Setup
let recognition = null;
let isListening = false;

// Initialize Speech Recognition (Web Speech API)
function initVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            isListening = true;
            document.getElementById('voiceButton').classList.add('listening');
            document.getElementById('voiceIcon').classList.remove('bi-mic-fill');
            document.getElementById('voiceIcon').classList.add('bi-mic-mute-fill');
            document.getElementById('voiceStatus').style.display = 'block';
            document.getElementById('voiceStatusText').textContent = 'Listening...';
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('aiMessageInput').value = transcript;
            document.getElementById('voiceStatusText').textContent = 'Got it! Processing...';
            
            // Auto-submit after getting voice input
            setTimeout(() => {
                document.getElementById('aiChatForm').dispatchEvent(new Event('submit'));
            }, 500);
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            let errorMsg = 'Error occurred';
            
            switch(event.error) {
                case 'no-speech':
                    errorMsg = 'No speech detected. Try again.';
                    break;
                case 'audio-capture':
                    errorMsg = 'No microphone found.';
                    break;
                case 'not-allowed':
                    errorMsg = 'Microphone access denied.';
                    break;
                default:
                    errorMsg = 'Voice recognition error.';
            }
            
            document.getElementById('voiceStatusText').textContent = errorMsg;
            setTimeout(() => {
                stopListening();
            }, 2000);
        };
        
        recognition.onend = function() {
            stopListening();
        };
    } else {
        console.warn('Speech recognition not supported in this browser');
        document.getElementById('voiceButton').style.display = 'none';
    }
}

function toggleVoiceInput() {
    if (!recognition) {
        initVoiceRecognition();
    }
    
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function stopListening() {
    isListening = false;
    document.getElementById('voiceButton').classList.remove('listening');
    document.getElementById('voiceIcon').classList.remove('bi-mic-mute-fill');
    document.getElementById('voiceIcon').classList.add('bi-mic-fill');
    setTimeout(() => {
        document.getElementById('voiceStatus').style.display = 'none';
    }, 2000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initVoiceRecognition();
});

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
        // Stop listening if voice is active
        if (isListening && recognition) {
            recognition.stop();
        }
    }
}

function sendAIMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById('aiMessageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Stop voice recognition if active
    if (isListening && recognition) {
        recognition.stop();
    }
    
    // Disable input while processing
    input.disabled = true;
    document.getElementById('sendButton').disabled = true;
    document.getElementById('voiceButton').disabled = true;
    
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
        
        // Re-enable input
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
        document.getElementById('voiceButton').disabled = false;
        input.focus();
    })
    .catch(error => {
        removeTypingIndicator();
        addMessageToChat('Sorry, I encountered an error processing your request. Please try again.', 'bot');
        console.error('AI Chat Error:', error);
        
        // Re-enable input
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
        document.getElementById('voiceButton').disabled = false;
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
                    <img src="/static/chatbot-icon.png" alt="AI" style="width: 24px; height: 24px; object-fit: contain;">
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
                <img src="/static/chatbot-icon.png" alt="AI" style="width: 24px; height: 24px; object-fit: contain;">
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