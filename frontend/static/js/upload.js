// Upload page specific functionality
class UploadPage {
    constructor() {
        this.init();
        this.setupFileUpload();
        this.setupForm();
        this.setupAuthModal();
        this.checkAuthStatus();
    }

    init() {
        this.selectedFile = null;
        this.isUploading = false;
        this.isAuthenticated = false;
        this.maxFileSize = 500 * 1024 * 1024; // 500MB
        
        // Supported file types
        this.supportedAudio = ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'];
        this.supportedVideo = ['mp4', 'webm', 'avi', 'mov', 'mkv', 'wmv'];
        this.allSupported = [...this.supportedAudio, ...this.supportedVideo];
        
        console.log('📤 Upload page initialized');
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status');
            if (response.ok) {
                const data = await response.json();
                this.isAuthenticated = data.authenticated;
                
                if (this.isAuthenticated) {
                    this.showUploadForm();
                } else {
                    this.showAuthPrompt();
                }
            } else {
                this.showAuthPrompt();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showAuthPrompt();
        }
    }

    showAuthPrompt() {
        const uploadContainer = document.querySelector('.upload-container');
        if (!uploadContainer) return;

        uploadContainer.innerHTML = `
            <div class="auth-prompt">
                <div class="auth-card">
                    <h2>🤖 Join AI Media Platform</h2>
                    <p>Create an account to upload and share your AI-generated content with the world!</p>
                    
                    <div class="auth-benefits">
                        <h3>✨ What you can do:</h3>
                        <ul>
                            <li>📤 Upload AI-generated audio and video content</li>
                            <li>🎵 Get your content featured on the live stream</li>
                            <li>📊 Track your content's performance</li>
                            <li>🤖 Receive AI-generated DJ introductions</li>
                            <li>💬 Engage with the community</li>
                        </ul>
                    </div>

                    <div class="auth-actions">
                        <button class="btn btn-primary" onclick="uploadPage.showSignupModal()">
                            Create Account
                        </button>
                        <button class="btn btn-secondary" onclick="uploadPage.showLoginModal()">
                            Sign In
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    showUploadForm() {
        // Upload form is already in the HTML, just ensure it's visible
        const uploadContainer = document.querySelector('.upload-container');
        if (uploadContainer && uploadContainer.querySelector('.auth-prompt')) {
            location.reload(); // Reload to show the original upload form
        }
    }

    setupAuthModal() {
        // Create auth modals
        this.createAuthModals();
    }

    createAuthModals() {
        // Signup Modal
        const signupModal = document.createElement('div');
        signupModal.id = 'signupModal';
        signupModal.className = 'modal';
        signupModal.style.display = 'none';
        signupModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Create Account</h2>
                    <button class="modal-close" onclick="uploadPage.closeModal('signupModal')">&times;</button>
                </div>
                <form class="modal-form" id="signupForm">
                    <div class="form-group">
                        <label for="signupUsername">Username</label>
                        <input type="text" id="signupUsername" name="username" required 
                               placeholder="Choose a unique username" maxlength="50">
                    </div>
                    <div class="form-group">
                        <label for="signupEmail">Email</label>
                        <input type="email" id="signupEmail" name="email" required 
                               placeholder="your@email.com">
                    </div>
                    <div class="form-group">
                        <label for="signupPassword">Password</label>
                        <input type="password" id="signupPassword" name="password" required 
                               placeholder="Create a strong password" minlength="8">
                    </div>
                    <div class="form-group">
                        <label for="signupConfirmPassword">Confirm Password</label>
                        <input type="password" id="signupConfirmPassword" name="confirmPassword" required 
                               placeholder="Confirm your password">
                    </div>
                    <div class="checkbox-group">
                        <label class="checkbox-label required">
                            <input type="checkbox" id="agreeTermsSignup" required>
                            <span class="checkmark"></span>
                            I agree to the <a href="/terms" target="_blank">Terms of Service</a> and 
                            <a href="/privacy" target="_blank">Privacy Policy</a>
                        </label>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" onclick="uploadPage.closeModal('signupModal')">Cancel</button>
                        <button type="submit" class="btn btn-primary">Create Account</button>
                    </div>
                </form>
            </div>
        `;

        // Login Modal
        const loginModal = document.createElement('div');
        loginModal.id = 'loginModal';
        loginModal.className = 'modal';
        loginModal.style.display = 'none';
        loginModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Sign In</h2>
                    <button class="modal-close" onclick="uploadPage.closeModal('loginModal')">&times;</button>
                </div>
                <form class="modal-form" id="loginForm">
                    <div class="form-group">
                        <label for="loginEmail">Email or Username</label>
                        <input type="text" id="loginEmail" name="login" required 
                               placeholder="Enter your email or username">
                    </div>
                    <div class="form-group">
                        <label for="loginPassword">Password</label>
                        <input type="password" id="loginPassword" name="password" required 
                               placeholder="Enter your password">
                    </div>
                    <div class="checkbox-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="rememberMe" name="remember">
                            <span class="checkmark"></span>
                            Remember me
                        </label>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" onclick="uploadPage.closeModal('loginModal')">Cancel</button>
                        <button type="submit" class="btn btn-primary">Sign In</button>
                    </div>
                </form>
                <div class="auth-links">
                    <a href="#" onclick="uploadPage.showForgotPassword()">Forgot password?</a>
                </div>
            </div>
        `;

        document.body.appendChild(signupModal);
        document.body.appendChild(loginModal);

        // Setup form handlers
        document.getElementById('signupForm').addEventListener('submit', (e) => this.handleSignup(e));
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
    }

    showSignupModal() {
        document.getElementById('signupModal').style.display = 'flex';
    }

    showLoginModal() {
        document.getElementById('loginModal').style.display = 'flex';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        
        if (password !== confirmPassword) {
            aiPlatform.showNotification('Passwords do not match', 'error');
            return;
        }

        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: formData.get('username'),
                    email: formData.get('email'),
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                aiPlatform.showNotification('Account created successfully! Please check your email for verification.', 'success');
                this.closeModal('signupModal');
                this.isAuthenticated = true;
                this.showUploadForm();
            } else {
                aiPlatform.showNotification(data.error || 'Signup failed', 'error');
            }
        } catch (error) {
            console.error('Signup error:', error);
            aiPlatform.showNotification('Signup failed. Please try again.', 'error');
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    login: formData.get('login'),
                    password: formData.get('password'),
                    remember: formData.get('remember') === 'on'
                })
            });

            const data = await response.json();

            if (response.ok) {
                aiPlatform.showNotification('Signed in successfully!', 'success');
                this.closeModal('loginModal');
                this.isAuthenticated = true;
                this.showUploadForm();
            } else {
                aiPlatform.showNotification(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            aiPlatform.showNotification('Login failed. Please try again.', 'error');
        }
    }

    setupFileUpload() {
        const fileDropZone = document.getElementById('fileDropZone');
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.querySelector('.browse-btn');
        const filePreview = document.getElementById('filePreview');
        const removeFile = document.getElementById('removeFile');

        if (!fileDropZone || !fileInput) return;

        // Browse button click
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                fileInput.click();
            });
        }

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        // Drag and drop events
        fileDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileDropZone.classList.add('dragover');
        });

        fileDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('dragover');
        });

        fileDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // Remove file button
        if (removeFile) {
            removeFile.addEventListener('click', () => {
                this.clearFile();
            });
        }

        // Make drop zone clickable
        fileDropZone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    handleFileSelect(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }

        this.selectedFile = file;
        this.showFilePreview(file);
        this.autoDetectMediaType(file);
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            aiPlatform.showNotification(`File too large. Maximum size is ${this.maxFileSize / (1024*1024)}MB`, 'error');
            return false;
        }

        // Check file type
        const extension = file.name.split('.').pop().toLowerCase();
        if (!this.allSupported.includes(extension)) {
            aiPlatform.showNotification(`Unsupported file type: ${extension}`, 'error');
            return false;
        }

        return true;
    }

    showFilePreview(file) {
        const filePreview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const fileDropZone = document.getElementById('fileDropZone');

        if (!filePreview || !fileName || !fileSize) return;

        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);
        
        filePreview.style.display = 'block';
        fileDropZone.style.display = 'none';

        // Show preview based on file type
        this.showMediaPreview(file);
    }

    showMediaPreview(file) {
        const extension = file.name.split('.').pop().toLowerCase();
        const previewContainer = document.createElement('div');
        previewContainer.className = 'media-preview';
        previewContainer.style.marginTop = '1rem';

        if (this.supportedVideo.includes(extension)) {
            // Video preview
            const video = document.createElement('video');
            video.controls = true;
            video.style.width = '100%';
            video.style.maxHeight = '300px';
            video.style.borderRadius = '10px';
            video.src = URL.createObjectURL(file);
            
            previewContainer.appendChild(video);
        } else if (this.supportedAudio.includes(extension)) {
            // Audio preview
            const audio = document.createElement('audio');
            audio.controls = true;
            audio.style.width = '100%';
            audio.src = URL.createObjectURL(file);
            
            previewContainer.appendChild(audio);
        }

        // Add to file preview
        const existingPreview = document.querySelector('.media-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        const filePreview = document.getElementById('filePreview');
        filePreview.appendChild(previewContainer);
    }

    autoDetectMediaType(file) {
        const extension = file.name.split('.').pop().toLowerCase();
        const mediaTypeSelect = document.getElementById('mediaType');
        
        if (!mediaTypeSelect) return;

        if (this.supportedVideo.includes(extension)) {
            mediaTypeSelect.value = 'video';
        } else if (this.supportedAudio.includes(extension)) {
            mediaTypeSelect.value = 'audio';
        }

        // Trigger change event to update UI
        mediaTypeSelect.dispatchEvent(new Event('change'));
    }

    clearFile() {
        this.selectedFile = null;
        
        const filePreview = document.getElementById('filePreview');
        const fileDropZone = document.getElementById('fileDropZone');
        const fileInput = document.getElementById('fileInput');
        const mediaPreview = document.querySelector('.media-preview');

        if (filePreview) filePreview.style.display = 'none';
        if (fileDropZone) fileDropZone.style.display = 'block';
        if (fileInput) fileInput.value = '';
        if (mediaPreview) mediaPreview.remove();
    }

    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Byte';
        
        const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    setupForm() {
        const uploadForm = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const resetBtn = document.getElementById('resetForm');
        const descriptionTextarea = document.getElementById('description');
        const descCharCount = document.getElementById('descCharCount');
        const tagsInput = document.getElementById('tags');

        if (!uploadForm) return;

        // Form submission
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmission();
        });

        // Reset form
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetForm();
            });
        }

        // Character counter for description
        if (descriptionTextarea && descCharCount) {
            descriptionTextarea.addEventListener('input', () => {
                const count = descriptionTextarea.value.length;
                descCharCount.textContent = count;
                
                if (count > 950) {
                    descCharCount.style.color = '#ff4569';
                } else if (count > 800) {
                    descCharCount.style.color = '#ffc107';
                } else {
                    descCharCount.style.color = '#82b1ff';
                }
            });
        }

        // Tag suggestions
        this.setupTagSuggestions();
    }

    setupTagSuggestions() {
        const tagsInput = document.getElementById('tags');
        const tagSuggestions = document.querySelectorAll('.tag-suggestion');

        if (!tagsInput) return;

        tagSuggestions.forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                const tag = suggestion.dataset.tag;
                const currentTags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t);
                
                if (!currentTags.includes(tag)) {
                    currentTags.push(tag);
                    tagsInput.value = currentTags.join(', ');
                }
            });
        });
    }

    async handleFormSubmission() {
        if (!this.isAuthenticated) {
            this.showSignupModal();
            return;
        }

        if (!this.selectedFile) {
            aiPlatform.showNotification('Please select a file to upload', 'error');
            return;
        }

        if (this.isUploading) {
            return;
        }

        this.isUploading = true;
        
        const submitBtn = document.getElementById('submitBtn');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        // Update button state
        submitBtn.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'inline-block';

        try {
            // Prepare form data
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('title', document.getElementById('title').value);
            formData.append('description', document.getElementById('description').value);
            formData.append('media_type', document.getElementById('mediaType').value);
            formData.append('category', document.getElementById('category').value);
            formData.append('ai_model', document.getElementById('aiModel').value);
            formData.append('prompt', document.getElementById('prompt').value);
            formData.append('tags', document.getElementById('tags').value);
            
            // Publishing options
            formData.append('allow_streaming', document.querySelector('input[name="allow_streaming"]').checked);
            formData.append('allow_download', document.querySelector('input[name="allow_download"]').checked);
            formData.append('featured_content', document.querySelector('input[name="featured_content"]').checked);

            // Upload with progress
            await this.uploadWithProgress(formData);
            
        } catch (error) {
            console.error('Upload error:', error);
            aiPlatform.showNotification('Upload failed. Please try again.', 'error');
        } finally {
            this.isUploading = false;
            
            // Reset button state
            submitBtn.disabled = false;
            if (btnText) btnText.style.display = 'inline-block';
            if (btnLoader) btnLoader.style.display = 'none';
        }
    }

    async uploadWithProgress(formData) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const uploadProgress = document.getElementById('uploadProgress');

            // Show progress bar
            if (uploadProgress) {
                uploadProgress.style.display = 'block';
            }

            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    
                    if (progressFill) {
                        progressFill.style.width = percentComplete + '%';
                    }
                    if (progressText) {
                        progressText.textContent = Math.round(percentComplete) + '%';
                    }
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        aiPlatform.showNotification('Upload successful! Your content is being processed.', 'success');
                        this.resetForm();
                        
                        // Redirect to dashboard after a delay
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 2000);
                        
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid response format'));
                    }
                } else {
                    try {
                        const error = JSON.parse(xhr.responseText);
                        reject(new Error(error.error || 'Upload failed'));
                    } catch {
                        reject(new Error('Upload failed'));
                    }
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });

            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });
    }

    resetForm() {
        const form = document.getElementById('uploadForm');
        if (form) {
            form.reset();
        }
        
        this.clearFile();
        
        // Reset character counter
        const descCharCount = document.getElementById('descCharCount');
        if (descCharCount) {
            descCharCount.textContent = '0';
            descCharCount.style.color = '#82b1ff';
        }

        // Hide progress bar
        const uploadProgress = document.getElementById('uploadProgress');
        if (uploadProgress) {
            uploadProgress.style.display = 'none';
        }

        aiPlatform.showNotification('Form reset', 'info');
    }

    showForgotPassword() {
        this.closeModal('loginModal');
        aiPlatform.showNotification('Password reset feature coming soon!', 'info');
    }
}

// Initialize upload page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/upload') {
        window.uploadPage = new UploadPage();
    }
});