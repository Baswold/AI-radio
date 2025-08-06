// Stream page specific functionality
class StreamPage {
    constructor() {
        this.init();
        this.setupStreamPlayer();
        this.setupChat();
        this.setupQualitySelector();
    }

    init() {
        this.isStreamLoaded = false;
        this.chatMessages = [];
        this.currentQuality = 'high';
        
        console.log('🎵 Stream page initialized');
    }

    setupStreamPlayer() {
        const liveStream = document.getElementById('liveStream');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const volumeSlider = document.getElementById('volumeSlider');
        const volumeValue = document.getElementById('volumeValue');

        if (!liveStream) return;

        // Enhanced stream player events
        liveStream.addEventListener('loadstart', () => {
            console.log('Live stream loading...');
            this.updatePlayerUI('loading');
        });

        liveStream.addEventListener('canplay', () => {
            console.log('Live stream ready to play');
            this.isStreamLoaded = true;
            this.updatePlayerUI('ready');
        });

        liveStream.addEventListener('playing', () => {
            console.log('Live stream playing');
            this.updatePlayerUI('playing');
        });

        liveStream.addEventListener('pause', () => {
            console.log('Live stream paused');
            this.updatePlayerUI('paused');
        });

        liveStream.addEventListener('error', (e) => {
            console.error('Live stream error:', e);
            this.updatePlayerUI('error');
            this.handleStreamError();
        });

        liveStream.addEventListener('waiting', () => {
            console.log('Live stream buffering...');
            this.updatePlayerUI('buffering');
        });

        // Play/Pause button
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                this.toggleLiveStream();
            });
        }

        // Volume control
        if (volumeSlider) {
            volumeSlider.addEventListener('input', (e) => {
                const volume = e.target.value;
                liveStream.volume = volume / 100;
                if (volumeValue) {
                    volumeValue.textContent = `${volume}%`;
                }
            });

            // Set initial volume
            liveStream.volume = volumeSlider.value / 100;
            if (volumeValue) {
                volumeValue.textContent = `${volumeSlider.value}%`;
            }
        }

        // Auto-retry on error
        liveStream.addEventListener('stalled', () => {
            setTimeout(() => {
                if (!liveStream.paused) {
                    liveStream.load();
                }
            }, 3000);
        });
    }

    async toggleLiveStream() {
        const liveStream = document.getElementById('liveStream');
        const playPauseBtn = document.getElementById('playPauseBtn');
        
        if (!liveStream || !playPauseBtn) return;

        try {
            if (liveStream.paused) {
                // Ensure stream source is set
                if (!liveStream.src || liveStream.src === '') {
                    liveStream.src = this.getStreamUrl();
                }
                
                await liveStream.play();
                playPauseBtn.textContent = '⏸️';
                aiPlatform.isPlaying = true;
            } else {
                liveStream.pause();
                playPauseBtn.textContent = '▶️';
                aiPlatform.isPlaying = false;
            }
        } catch (error) {
            console.error('Error toggling live stream:', error);
            this.handleStreamError();
        }
    }

    getStreamUrl() {
        const quality = this.currentQuality;
        const baseUrl = '/stream';
        
        // Return appropriate stream URL based on quality
        switch (quality) {
            case 'high':
                return `${baseUrl}?quality=192`;
            case 'medium':
                return `${baseUrl}?quality=128`;
            case 'low':
                return `${baseUrl}?quality=64`;
            default:
                return baseUrl;
        }
    }

    updatePlayerUI(state) {
        const playPauseBtn = document.getElementById('playPauseBtn');
        const playerCard = document.querySelector('.player-card');
        
        if (!playPauseBtn) return;

        // Remove all state classes
        if (playerCard) {
            playerCard.classList.remove('loading', 'playing', 'paused', 'error', 'buffering');
            playerCard.classList.add(state);
        }

        switch (state) {
            case 'loading':
                playPauseBtn.textContent = '⏳';
                playPauseBtn.disabled = true;
                break;
            case 'ready':
            case 'paused':
                playPauseBtn.textContent = '▶️';
                playPauseBtn.disabled = false;
                break;
            case 'playing':
                playPauseBtn.textContent = '⏸️';
                playPauseBtn.disabled = false;
                break;
            case 'buffering':
                playPauseBtn.textContent = '⏳';
                playPauseBtn.disabled = true;
                break;
            case 'error':
                playPauseBtn.textContent = '❌';
                playPauseBtn.disabled = true;
                setTimeout(() => {
                    playPauseBtn.textContent = '▶️';
                    playPauseBtn.disabled = false;
                }, 3000);
                break;
        }
    }

    handleStreamError() {
        aiPlatform.showNotification('Stream connection lost. Retrying...', 'error');
        
        // Auto-retry after 5 seconds
        setTimeout(() => {
            const liveStream = document.getElementById('liveStream');
            if (liveStream && !liveStream.paused) {
                liveStream.load();
                liveStream.play().catch(e => {
                    console.error('Auto-retry failed:', e);
                });
            }
        }, 5000);
    }

    setupChat() {
        const chatInput = document.getElementById('chatInput');
        const sendChat = document.getElementById('sendChat');
        const chatMessages = document.getElementById('chatMessages');

        if (!chatInput || !sendChat || !chatMessages) return;

        // Send chat message
        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (!message) return;

            this.addChatMessage({
                username: 'You',
                message: message,
                timestamp: new Date(),
                type: 'user'
            });

            chatInput.value = '';
            
            // Simulate AI response (replace with actual chat implementation)
            setTimeout(() => {
                this.addChatMessage({
                    username: 'AI DJ',
                    message: this.generateAIResponse(message),
                    timestamp: new Date(),
                    type: 'ai'
                });
            }, 1000 + Math.random() * 2000);
        };

        sendChat.addEventListener('click', sendMessage);
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Auto-scroll chat
        chatMessages.addEventListener('DOMNodeInserted', () => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });

        // Load initial chat messages
        this.loadChatHistory();
    }

    addChatMessage(messageData) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${messageData.type}`;
        
        const timestamp = this.formatTime(messageData.timestamp);
        const username = aiPlatform.escapeHtml(messageData.username);
        const message = aiPlatform.escapeHtml(messageData.message);

        messageElement.innerHTML = `
            <span class="timestamp">${timestamp}</span>
            <span class="username">${username}:</span>
            <span class="message">${message}</span>
        `;

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Keep only last 50 messages
        const messages = chatMessages.querySelectorAll('.chat-message');
        if (messages.length > 50) {
            messages[0].remove();
        }
    }

    generateAIResponse(userMessage) {
        const responses = [
            "Great taste in music! 🎵",
            "That's an interesting point!",
            "Thanks for listening to AI Radio! 🤖",
            "What kind of AI music do you enjoy most?",
            "The current track was generated using neural networks!",
            "AI creativity knows no bounds! ✨",
            "Hope you're enjoying the AI-generated content!",
            "Feel free to upload your own AI creations!"
        ];

        // Simple keyword responses
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('music') || lowerMessage.includes('song')) {
            return "🎵 All our music is 100% AI-generated! Pretty amazing, right?";
        }
        if (lowerMessage.includes('ai') || lowerMessage.includes('artificial')) {
            return "🤖 AI is creating incredible content these days! This platform showcases the best AI-generated media.";
        }
        if (lowerMessage.includes('upload')) {
            return "📤 You can upload your own AI-generated content using the Upload page!";
        }
        if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
            return "Hello there! Welcome to AI Radio! 👋";
        }

        return responses[Math.floor(Math.random() * responses.length)];
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/recent');
            if (response.ok) {
                const data = await response.json();
                data.messages?.forEach(msg => this.addChatMessage(msg));
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            
            // Add welcome message
            this.addChatMessage({
                username: 'AI DJ',
                message: 'Welcome to the live stream! Chat with other listeners here. 🎵',
                timestamp: new Date(),
                type: 'system'
            });
        }
    }

    setupQualitySelector() {
        const qualityOptions = document.querySelectorAll('input[name="quality"]');
        
        qualityOptions.forEach(option => {
            option.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.changeStreamQuality(e.target.value);
                }
            });
        });
    }

    changeStreamQuality(quality) {
        this.currentQuality = quality;
        const liveStream = document.getElementById('liveStream');
        
        if (liveStream && !liveStream.paused) {
            // Remember current time and playing state
            const wasPlaying = !liveStream.paused;
            
            // Change stream source
            liveStream.src = this.getStreamUrl();
            
            if (wasPlaying) {
                liveStream.play().catch(e => {
                    console.error('Error switching quality:', e);
                });
            }
        }

        aiPlatform.showNotification(`Stream quality changed to ${quality}`, 'success');
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Update stream info periodically
    startStreamUpdates() {
        setInterval(() => {
            this.updateStreamInfo();
        }, 10000); // Update every 10 seconds
    }

    async updateStreamInfo() {
        try {
            const response = await fetch('/api/stream/info');
            if (response.ok) {
                const data = await response.json();
                this.updateStreamDisplay(data);
            }
        } catch (error) {
            console.error('Error updating stream info:', error);
        }
    }

    updateStreamDisplay(data) {
        // Update listener count
        const listenerCount = document.getElementById('listenerCount');
        if (listenerCount && data.listeners !== undefined) {
            listenerCount.textContent = `${data.listeners} listeners`;
        }

        // Update stream status
        if (data.status) {
            const liveIndicator = document.querySelector('.live-indicator');
            if (liveIndicator) {
                liveIndicator.style.color = data.status === 'live' ? '#ff4569' : '#888';
            }
        }
    }
}

// Initialize stream page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on stream page
    if (window.location.pathname === '/stream') {
        window.streamPage = new StreamPage();
        window.streamPage.startStreamUpdates();
    }
});