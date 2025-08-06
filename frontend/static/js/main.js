// Main JavaScript functionality for AI Media Platform
class AIMediaPlatform {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.loadInitialData();
    }

    init() {
        // Initialize global variables
        this.currentUser = null;
        this.isPlaying = false;
        this.currentVolume = 50;
        this.updateInterval = null;
        
        // API endpoints
        this.API = {
            nowPlaying: '/api/now_playing',
            stats: '/api/stats',
            featured: '/api/featured',
            user: '/api/user'
        };
        
        console.log('🤖 AI Media Platform initialized');
    }

    setupEventListeners() {
        // Global event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeComponents();
        });

        // Stream player events
        const playBtn = document.getElementById('playBtn');
        const streamPlayer = document.getElementById('streamPlayer');
        const volumeSlider = document.getElementById('volumeSlider');

        if (playBtn) {
            playBtn.addEventListener('click', () => this.toggleStream());
        }

        if (streamPlayer) {
            streamPlayer.addEventListener('loadstart', () => {
                console.log('Stream loading started');
            });
            streamPlayer.addEventListener('canplay', () => {
                console.log('Stream can play');
            });
            streamPlayer.addEventListener('error', (e) => {
                console.error('Stream error:', e);
                this.handleStreamError();
            });
        }

        if (volumeSlider) {
            volumeSlider.addEventListener('input', (e) => {
                this.setVolume(e.target.value);
            });
        }

        // Navigation active state
        this.updateActiveNavigation();
    }

    initializeComponents() {
        // Initialize volume
        const volumeSlider = document.getElementById('volumeSlider');
        if (volumeSlider) {
            this.setVolume(volumeSlider.value);
        }

        // Start periodic updates
        this.startPeriodicUpdates();
        
        // Load page-specific data
        this.loadPageData();
    }

    async toggleStream() {
        const playBtn = document.getElementById('playBtn');
        const streamPlayer = document.getElementById('streamPlayer');
        
        if (!streamPlayer || !playBtn) return;

        try {
            if (this.isPlaying) {
                streamPlayer.pause();
                playBtn.textContent = '▶️';
                this.isPlaying = false;
                console.log('Stream paused');
            } else {
                // Set stream source
                if (!streamPlayer.src) {
                    streamPlayer.src = '/stream';
                }
                
                await streamPlayer.play();
                playBtn.textContent = '⏸️';
                this.isPlaying = true;
                console.log('Stream playing');
            }
        } catch (error) {
            console.error('Error toggling stream:', error);
            this.handleStreamError();
        }
    }

    setVolume(value) {
        this.currentVolume = value;
        const streamPlayer = document.getElementById('streamPlayer');
        const volumeValue = document.getElementById('volumeValue');
        
        if (streamPlayer) {
            streamPlayer.volume = value / 100;
        }
        
        if (volumeValue) {
            volumeValue.textContent = `${value}%`;
        }
        
        // Update volume icon
        const volumeIcon = document.querySelector('.volume-icon');
        if (volumeIcon) {
            if (value == 0) {
                volumeIcon.textContent = '🔇';
            } else if (value < 30) {
                volumeIcon.textContent = '🔉';
            } else {
                volumeIcon.textContent = '🔊';
            }
        }
    }

    handleStreamError() {
        const playBtn = document.getElementById('playBtn');
        if (playBtn) {
            playBtn.textContent = '❌';
            setTimeout(() => {
                playBtn.textContent = '▶️';
            }, 3000);
        }
        
        this.showNotification('Stream temporarily unavailable', 'error');
    }

    async loadNowPlaying() {
        try {
            const response = await fetch(this.API.nowPlaying);
            if (!response.ok) throw new Error('Failed to fetch now playing');
            
            const data = await response.json();
            this.updateNowPlayingDisplay(data);
        } catch (error) {
            console.error('Error loading now playing:', error);
            this.updateNowPlayingDisplay({
                title: 'Loading...',
                artist: 'AI DJ',
                description: 'Preparing next track...'
            });
        }
    }

    updateNowPlayingDisplay(data) {
        // Update track info elements
        const elements = {
            trackTitle: data.title || 'Unknown Track',
            trackArtist: data.artist || 'AI DJ',
            currentTitle: data.title || 'Unknown Track',
            currentArtist: data.artist || 'AI DJ',
            trackDescription: data.description || 'AI-generated content',
            currentGenre: data.genre || 'AI Electronic',
            currentDuration: data.duration || '0:00',
            aiModel: data.ai_model || 'GPT-OSS',
            generatedTime: data.generated_time || 'Recently'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update DJ intro if available
        if (data.dj_intro) {
            const djIntroSection = document.getElementById('djIntroSection');
            const djIntroText = document.getElementById('djIntroText');
            
            if (djIntroSection && djIntroText) {
                djIntroText.textContent = data.dj_intro;
                djIntroSection.style.display = 'block';
                
                // Auto-hide after 10 seconds
                setTimeout(() => {
                    djIntroSection.style.display = 'none';
                }, 10000);
            }
        }
    }

    async loadStats() {
        try {
            const response = await fetch(this.API.stats);
            if (!response.ok) throw new Error('Failed to fetch stats');
            
            const data = await response.json();
            this.updateStatsDisplay(data);
        } catch (error) {
            console.error('Error loading stats:', error);
            // Use default values
            this.updateStatsDisplay({
                total_tracks: 0,
                total_listeners: 0,
                hours_streamed: 0,
                ai_models: 5
            });
        }
    }

    updateStatsDisplay(data) {
        const statElements = {
            totalTracks: data.total_tracks || 0,
            totalListeners: data.total_listeners || 0,
            hoursStreamed: data.hours_streamed || 0,
            aiModels: data.ai_models || 5
        };

        Object.entries(statElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                // Animate number counting
                this.animateNumber(element, parseInt(element.textContent) || 0, value);
            }
        });

        // Update listener count
        const listenerCount = document.getElementById('listenerCount');
        if (listenerCount && data.current_listeners) {
            listenerCount.textContent = `${data.current_listeners} listeners`;
        }
    }

    animateNumber(element, start, end, duration = 1000) {
        const startTime = performance.now();
        const difference = end - start;

        function updateNumber(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (difference * progress));
            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        }

        requestAnimationFrame(updateNumber);
    }

    async loadFeaturedContent() {
        try {
            const response = await fetch(this.API.featured);
            if (!response.ok) throw new Error('Failed to fetch featured content');
            
            const data = await response.json();
            this.displayFeaturedContent(data.featured || []);
        } catch (error) {
            console.error('Error loading featured content:', error);
            this.displayFeaturedContent([]);
        }
    }

    displayFeaturedContent(items) {
        const container = document.getElementById('featuredGrid');
        if (!container) return;

        if (items.length === 0) {
            container.innerHTML = '<p class="no-content">No featured content available.</p>';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="content-item" data-id="${item.id}">
                <div class="content-thumbnail">
                    <div class="thumbnail-image">${this.getContentIcon(item.media_type)}</div>
                    <div class="play-overlay">
                        <button class="play-btn" onclick="aiPlatform.playContent('${item.id}')">▶️</button>
                    </div>
                    <div class="content-type-badge">${item.media_type}</div>
                    <div class="duration-badge">${item.duration || '0:00'}</div>
                </div>
                <div class="content-info">
                    <h3 class="content-title">${this.escapeHtml(item.title)}</h3>
                    <p class="content-creator">by ${this.escapeHtml(item.username)}</p>
                    <p class="content-description">${this.escapeHtml(item.description || '')}</p>
                    <div class="content-meta">
                        <span class="upload-date">${this.formatDate(item.uploaded_at)}</span>
                        <span class="play-count">👁️ ${item.played_count || 0} plays</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getContentIcon(mediaType) {
        const icons = {
            'audio': '🎵',
            'video': '📺',
            'podcast': '🎙️',
            'music': '🎵',
            'story': '📚'
        };
        return icons[mediaType] || '🎵';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (!dateString) return 'Recently';
        
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }

    playContent(contentId) {
        // This would typically play individual content
        console.log(`Playing content: ${contentId}`);
        this.showNotification('Feature coming soon!', 'info');
    }

    startPeriodicUpdates() {
        // Update now playing every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadNowPlaying();
        }, 30000);
        
        // Update stats every 5 minutes
        setInterval(() => {
            this.loadStats();
        }, 300000);
    }

    loadPageData() {
        const path = window.location.pathname;
        
        switch (path) {
            case '/':
                this.loadNowPlaying();
                this.loadStats();
                this.loadFeaturedContent();
                break;
            case '/stream':
                this.loadNowPlaying();
                this.loadQueueData();
                this.loadRecentTracks();
                break;
            default:
                this.loadNowPlaying();
        }
    }

    async loadQueueData() {
        try {
            const response = await fetch('/api/queue');
            if (!response.ok) throw new Error('Failed to fetch queue');
            
            const data = await response.json();
            this.displayQueue(data.queue || []);
        } catch (error) {
            console.error('Error loading queue:', error);
            this.displayQueue([]);
        }
    }

    displayQueue(items) {
        const container = document.getElementById('queueList');
        if (!container) return;

        if (items.length === 0) {
            container.innerHTML = '<p class="no-content">Queue is empty.</p>';
            return;
        }

        container.innerHTML = items.map((item, index) => `
            <div class="queue-item">
                <span class="queue-position">${index + 1}</span>
                <div class="queue-info">
                    <h4>${this.escapeHtml(item.title)}</h4>
                    <p>by ${this.escapeHtml(item.username)} • ${item.duration || '0:00'}</p>
                </div>
                <span class="queue-type">${this.getContentIcon(item.media_type)}</span>
            </div>
        `).join('');
    }

    async loadRecentTracks() {
        try {
            const response = await fetch('/api/recent');
            if (!response.ok) throw new Error('Failed to fetch recent tracks');
            
            const data = await response.json();
            this.displayRecentTracks(data.recent || []);
        } catch (error) {
            console.error('Error loading recent tracks:', error);
            this.displayRecentTracks([]);
        }
    }

    displayRecentTracks(items) {
        const container = document.getElementById('recentTracks');
        if (!container) return;

        if (items.length === 0) {
            container.innerHTML = '<p class="no-content">No recent tracks.</p>';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="track-item">
                <div class="track-icon">${this.getContentIcon(item.media_type)}</div>
                <div class="track-details">
                    <h4>${this.escapeHtml(item.title)}</h4>
                    <p>by ${this.escapeHtml(item.username)} • played ${this.formatDate(item.played_at)}</p>
                </div>
            </div>
        `).join('');
    }

    updateActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav a');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${this.escapeHtml(message)}</span>
            <button class="notification-close">&times;</button>
        `;

        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'error' ? 'rgba(244, 67, 54, 0.9)' : 
                       type === 'success' ? 'rgba(76, 175, 80, 0.9)' : 
                       'rgba(33, 150, 243, 0.9)',
            color: 'white',
            padding: '1rem 1.5rem',
            borderRadius: '10px',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
            zIndex: '9999',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            maxWidth: '400px',
            animation: 'slideIn 0.3s ease'
        });

        // Add close functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 1.2rem;
            padding: 0;
        `;
        
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        });

        // Add to document
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);

        // Add CSS animations if not already present
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Utility method to make API calls
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Cleanup method
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize the platform
const aiPlatform = new AIMediaPlatform();

// Export for use in other scripts
window.aiPlatform = aiPlatform;