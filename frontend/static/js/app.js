// Application State
let currentUser = null;
let currentLecture = null;
let authToken = localStorage.getItem('authToken');

// API Base URL
const API_BASE = '/api';

// DOM Elements
const loginSection = document.getElementById('login-section');
const registerSection = document.getElementById('register-section');
const dashboardSection = document.getElementById('dashboard-section');
const welcomeScreen = document.getElementById('welcome-screen');
const chatInterface = document.getElementById('chat-interface');
const uploadModal = document.getElementById('upload-modal');
const loadingOverlay = document.getElementById('loading-overlay');
const toastContainer = document.getElementById('toast-container');

// Initialize App
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
    setupEventListeners();
});

// Initialize Application
async function initializeApp() {
    if (authToken) {
        try {
            const user = await getCurrentUser();
            if (user) {
                currentUser = user;
                showDashboard();
                loadLectures();
            } else {
                showLogin();
            }
        } catch (error) {
            console.error('Error initializing app:', error);
            showLogin();
        }
    } else {
        showLogin();
    }
}

// Event Listeners
function setupEventListeners() {
    // Auth form handlers
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('show-register').addEventListener('click', showRegister);
    document.getElementById('show-login').addEventListener('click', showLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // Upload modal handlers
    document.getElementById('upload-btn').addEventListener('click', showUploadModal);
    document.getElementById('close-upload-modal').addEventListener('click', hideUploadModal);
    document.getElementById('cancel-upload').addEventListener('click', hideUploadModal);
    document.getElementById('upload-form').addEventListener('submit', handleUpload);

    // Chat handlers
    document.getElementById('chat-form').addEventListener('submit', handleChatMessage);
    document.getElementById('summarize-btn').addEventListener('click', handleSummarize);

    // Click outside modal to close
    uploadModal.addEventListener('click', function (e) {
        if (e.target === uploadModal) {
            hideUploadModal();
        }
    });
}

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    showLoading();

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);

            const user = await getCurrentUser();
            currentUser = user;

            showToast('Login successful!', 'success');
            showDashboard();
            loadLectures();
        } else {
            showToast(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Login failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function handleRegister(e) {
    e.preventDefault();
    showLoading();

    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password }),
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Registration successful! Please login.', 'success');
            showLogin();
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Registration failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function getCurrentUser() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error getting current user:', error);
        return null;
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    currentLecture = null;
    localStorage.removeItem('authToken');
    showLogin();
    showToast('Logged out successfully', 'info');
}

// UI Navigation Functions
function showLogin() {
    loginSection.style.display = 'block';
    registerSection.style.display = 'none';
    dashboardSection.style.display = 'none';
    document.getElementById('logout-btn').style.display = 'none';
}

function showRegister() {
    loginSection.style.display = 'none';
    registerSection.style.display = 'block';
    dashboardSection.style.display = 'none';
    document.getElementById('logout-btn').style.display = 'none';
}

function showDashboard() {
    loginSection.style.display = 'none';
    registerSection.style.display = 'none';
    dashboardSection.style.display = 'block';
    document.getElementById('logout-btn').style.display = 'block';

    // Show welcome screen initially
    welcomeScreen.style.display = 'flex';
    chatInterface.style.display = 'none';
}

function showUploadModal() {
    uploadModal.style.display = 'flex';
}

function hideUploadModal() {
    uploadModal.style.display = 'none';
    document.getElementById('upload-form').reset();
}

// Lecture Functions
async function loadLectures() {
    try {
        const response = await fetch(`${API_BASE}/lectures/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            const lectures = await response.json();
            displayLectures(lectures);
        } else {
            showToast('Failed to load lectures', 'error');
        }
    } catch (error) {
        console.error('Error loading lectures:', error);
        showToast('Failed to load lectures', 'error');
    }
}

function displayLectures(lectures) {
    const lectureList = document.getElementById('lecture-list');
    lectureList.innerHTML = '';

    if (lectures.length === 0) {
        lectureList.innerHTML = '<p class="no-lectures">No lectures uploaded yet. Upload your first lecture to get started!</p>';
        return;
    }

    lectures.forEach(lecture => {
        const lectureItem = document.createElement('div');
        lectureItem.className = 'lecture-item';
        lectureItem.dataset.lectureId = lecture.id;

        const statusClass = `status-${lecture.transcript_status}`;
        const statusText = lecture.transcript_status.charAt(0).toUpperCase() + lecture.transcript_status.slice(1);

        lectureItem.innerHTML = `
            <h4>${lecture.title}</h4>
            <p>${lecture.description || 'No description'}</p>
            <span class="lecture-status ${statusClass}">${statusText}</span>
        `;

        lectureItem.addEventListener('click', () => selectLecture(lecture));
        lectureList.appendChild(lectureItem);
    });
}

function selectLecture(lecture) {
    currentLecture = lecture;

    // Update active state
    document.querySelectorAll('.lecture-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-lecture-id="${lecture.id}"]`).classList.add('active');

    // Show chat interface
    if (lecture.transcript_status === 'completed') {
        welcomeScreen.style.display = 'none';
        chatInterface.style.display = 'flex';
        document.getElementById('current-lecture-title').textContent = lecture.title;
        loadChatHistory(lecture.id);
    } else {
        showToast('Lecture transcript is not ready yet. Please wait for processing to complete.', 'warning');
    }
}

async function handleUpload(e) {
    e.preventDefault();
    showLoading();

    const formData = new FormData();
    formData.append('title', document.getElementById('video-title').value);
    formData.append('description', document.getElementById('video-description').value);
    formData.append('video', document.getElementById('video-file').files[0]);

    try {
        const response = await fetch(`${API_BASE}/lectures/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
            body: formData,
        });

        if (response.ok) {
            showToast('Video uploaded successfully! Processing will begin shortly.', 'success');
            hideUploadModal();
            loadLectures();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Chat Functions
async function handleChatMessage(e) {
    e.preventDefault();

    if (!currentLecture) {
        showToast('Please select a lecture first', 'warning');
        return;
    }

    const messageInput = document.getElementById('chat-input-field');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat(message, 'user');
    messageInput.value = '';

    // Show typing indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify({
                message: message,
                lecture_id: currentLecture.id,
            }),
        });

        if (response.ok) {
            const data = await response.json();
            removeTypingIndicator(typingIndicator);
            addMessageToChat(data.response, 'bot', data.timestamp_references);
        } else {
            const error = await response.json();
            removeTypingIndicator(typingIndicator);
            showToast(error.detail || 'Failed to get response', 'error');
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator(typingIndicator);
        showToast('Failed to send message', 'error');
    }
}

function addMessageToChat(message, sender, timestampRefs = []) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : 'AI';

    const content = document.createElement('div');
    content.className = 'message-content';

    const text = document.createElement('div');
    text.className = 'message-text';
    text.textContent = message;
    content.appendChild(text);

    // Add timestamp references for bot messages
    if (sender === 'bot' && timestampRefs.length > 0) {
        const sources = document.createElement('div');
        sources.className = 'message-sources';

        const sourcesTitle = document.createElement('h5');
        sourcesTitle.textContent = 'Jump to relevant moments:';
        sources.appendChild(sourcesTitle);

        timestampRefs.forEach(ref => {
            const link = document.createElement('a');
            link.className = 'timestamp-link';
            link.href = '#';
            link.textContent = `${formatTimestamp(ref.start_time)} - ${formatTimestamp(ref.end_time)}`;
            link.addEventListener('click', (e) => {
                e.preventDefault();
                // TODO: Implement video player integration
                showToast(`Jump to ${formatTimestamp(ref.start_time)}`, 'info');
            });
            sources.appendChild(link);
        });

        content.appendChild(sources);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-text">Thinking...</div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingDiv;
}

function removeTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
    }
}

async function loadChatHistory(lectureId) {
    try {
        const response = await fetch(`${API_BASE}/chat/history/${lectureId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            const history = await response.json();
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';

            history.reverse().forEach(chat => {
                addMessageToChat(chat.user_message, 'user');
                addMessageToChat(chat.bot_response, 'bot', chat.timestamp_references);
            });
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

async function handleSummarize() {
    if (!currentLecture) {
        showToast('Please select a lecture first', 'warning');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/chat/summarize/${currentLecture.id}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            const data = await response.json();
            addMessageToChat('Please provide a summary of this lecture.', 'user');
            addMessageToChat(data.summary, 'bot');
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to generate summary', 'error');
        }
    } catch (error) {
        console.error('Summarize error:', error);
        showToast('Failed to generate summary', 'error');
    } finally {
        hideLoading();
    }
}

// Utility Functions
function formatTimestamp(seconds) {
    if (!seconds) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);

    // Click to dismiss
    toast.addEventListener('click', () => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    });
} 