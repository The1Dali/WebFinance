// ============================================================================
// VOICE RECORDING (MediaRecorder - works in ALL browsers including Firefox)
// ============================================================================

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let stream = null;

// Initialize MediaRecorder for cross-browser voice support
async function initVoiceRecording() {
    try {
        // Request microphone access
        stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        // Determine best audio format for browser
        let mimeType = 'audio/webm;codecs=opus';
        
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            mimeType = 'audio/webm';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/ogg;codecs=opus';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4';
                }
            }
        }
        
        console.log(`Using audio format: ${mimeType}`);
        
        // Create MediaRecorder
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: mimeType,
            audioBitsPerSecond: 128000
        });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
            audioChunks = [];
            
            // Send audio to backend for transcription
            await transcribeAudio(audioBlob);
        };
        
        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            alert('Recording error: ' + event.error);
        };
        
        return true;
    } catch (error) {
        console.error('Microphone access error:', error);
        
        if (error.name === 'NotAllowedError') {
            alert('Microphone access denied. Please allow microphone access in your browser settings.');
        } else if (error.name === 'NotFoundError') {
            alert('No microphone found. Please connect a microphone.');
        } else {
            alert('Error accessing microphone: ' + error.message);
        }
        
        return false;
    }
}

// Toggle voice input (start/stop recording)
async function toggleVoiceInput() {
    const voiceButton = document.getElementById('voiceButton');
    const voiceIcon = document.getElementById('voiceIcon');
    const voiceStatus = document.getElementById('voiceStatus');
    const voiceStatusText = document.getElementById('voiceStatusText');
    
    if (!isRecording) {
        // Start recording
        if (!mediaRecorder) {
            const initialized = await initVoiceRecording();
            if (!initialized) return;
        }
        
        try {
            audioChunks = [];
            mediaRecorder.start();
            isRecording = true;
            
            voiceButton.classList.add('listening');
            voiceIcon.classList.remove('bi-mic-fill');
            voiceIcon.classList.add('bi-mic-mute-fill');
            voiceStatus.style.display = 'block';
            voiceStatusText.textContent = 'Recording... Click again to stop';
            
            console.log('Recording started');
        } catch (error) {
            console.error('Start recording error:', error);
            alert('Failed to start recording: ' + error.message);
        }
        
    } else {
        // Stop recording
        try {
            mediaRecorder.stop();
            isRecording = false;
            
            voiceButton.classList.remove('listening');
            voiceIcon.classList.remove('bi-mic-mute-fill');
            voiceIcon.classList.add('bi-mic-fill');
            voiceStatusText.textContent = 'Processing audio...';
            
            console.log('Recording stopped');
        } catch (error) {
            console.error('Stop recording error:', error);
            voiceStatus.style.display = 'none';
        }
    }
}

// Send audio to backend for transcription
async function transcribeAudio(audioBlob) {
    const voiceStatusText = document.getElementById('voiceStatusText');
    const voiceStatus = document.getElementById('voiceStatus');
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        voiceStatusText.textContent = 'Transcribing...';
        
        console.log('Sending audio to server...', audioBlob.size, 'bytes');
        
        const response = await fetch('/api/speech-to-text', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Transcription failed');
        }
        
        const data = await response.json();
        
        if (data.success && data.transcription) {
            console.log('Transcription:', data.transcription);
            
            // Put transcription in input field
            document.getElementById('aiMessageInput').value = data.transcription;
            voiceStatusText.textContent = 'Got it! Sending...';
            
            // IMPORTANT: Call sendAIMessage directly, don't dispatch event
            setTimeout(() => {
                voiceStatus.style.display = 'none';
                // Create a fake event object
                const fakeEvent = { preventDefault: () => {} };
                sendAIMessage(fakeEvent);  // ← CHANGED: Call function directly
            }, 500);
        } else {
            throw new Error('No transcription received');
        }
        
    } catch (error) {
        console.error('Transcription error:', error);
        voiceStatusText.textContent = 'Failed to transcribe: ' + error.message;
        setTimeout(() => {
            voiceStatus.style.display = 'none';
        }, 3000);
    }
}

// ============================================================================
// CHAT FUNCTIONS
// ============================================================================

function toggleAIChat() {
    const chatWindow = document.getElementById('aiChatWindow');
    const toggleBtn = document.getElementById('aiToggleBtn');
    
    if (chatWindow.style.display === 'none' || !chatWindow.style.display) {
        chatWindow.style.display = 'block';
        toggleBtn.style.display = 'none';
        setTimeout(() => {
            document.getElementById('aiMessageInput').focus();
        }, 100);
    } else {
        chatWindow.style.display = 'none';
        toggleBtn.style.display = 'flex';
        
        // Stop recording if active
        if (isRecording && mediaRecorder) {
            mediaRecorder.stop();
            isRecording = false;
            document.getElementById('voiceButton').classList.remove('listening');
            document.getElementById('voiceIcon').classList.remove('bi-mic-mute-fill');
            document.getElementById('voiceIcon').classList.add('bi-mic-fill');
            document.getElementById('voiceStatus').style.display = 'none';
        }
    }
}

function sendAIMessage(event) {
    event.preventDefault(); // ← Make sure this is here!
    
    const input = document.getElementById('aiMessageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Stop recording if active
    if (isRecording && mediaRecorder) {
        mediaRecorder.stop();
        isRecording = false;
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
    .then(response => {
        if (!response.ok) {
            throw new Error('Server error: ' + response.status);
        }
        return response.json();
    })
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
        console.error('AI Chat Error:', error);
        addMessageToChat('Sorry, I encountered an error processing your request. Please make sure the AI service is running and try again.', 'bot');
        
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
                    <img src="/static/advisor.png" alt="AI" style="width: 50px; height: 50px; object-fit: contain;">
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
                <img src="/static/advisor.png" alt="AI" style="width: 50px; height: 50px; object-fit: contain;">
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

// ============================================================================
// CLEANUP ON PAGE UNLOAD
// ============================================================================

window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});

console.log('AI Advisor loaded successfully!');