import * as api from './api.js';
import {
    activeConversationId,
    setActiveConversationId,
    conversations,
    loadConversations,
    selectConversation,
    createNewConversation,
    deleteConversation
} from './conversation.js';

let currentAbortController = null;

// Escape HTML helper
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Show custom chat alert
export function showChatAlert(message, type) {
    const alertBox = document.getElementById('chatAlertBox');
    const alertIcon = document.getElementById('chatAlertIcon');
    const alertMessage = document.getElementById('chatAlertMessage');
    if (!alertBox) return;

    alertMessage.innerHTML = message;
    alertBox.classList.remove('d-none');

    if (type === 'success') {
        alertBox.className = 'alert alert-custom alert-success';
        alertIcon.className = 'bi bi-check-circle-fill text-success';
    } else {
        alertBox.className = 'alert alert-custom alert-danger';
        alertIcon.className = 'bi bi-exclamation-triangle-fill text-danger';
    }

    alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Fetch and Load Messages of active session
export async function loadMessages(convId, signal) {
    const token = getToken();
    const messagesBox = document.getElementById("messagesBox");
    if (!messagesBox) return;
    messagesBox.innerHTML = `
        <div class="text-center py-5 text-secondary opacity-50">
            <span class="spinner-border spinner-border-sm" role="status"></span>
        </div>
    `;

    try {
        const response = await api.listMessages(token, convId, signal);

        if (response.ok) {
            const messages = await response.json();
            renderMessages(messages);
        } else {
            showChatAlert('Không thể tải tin nhắn hội thoại.', 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Lỗi tải tin nhắn:', error);
        showChatAlert('Lỗi kết nối mạng.', 'error');
    }
}

export function stopGenerating() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;

        document.getElementById("typingIndicator").classList.add('d-none');
        const btnStop = document.getElementById("btnStopGenerating");
        if (btnStop) btnStop.classList.add('d-none');
    }
}

export async function regenerateResponse(signal) {
    if (!activeConversationId) return;
    document.getElementById('chatAlertBox').classList.add('d-none');
    const token = getToken();
    const typingIndicator = document.getElementById("typingIndicator");
    const btnStop = document.getElementById("btnStopGenerating");

    typingIndicator.classList.remove('d-none');
    if (btnStop) btnStop.classList.remove('d-none');

    currentAbortController = new AbortController();
    const fetchSignal = signal || currentAbortController.signal;

    try {
        const response = await api.regenerateResponse(token, activeConversationId, fetchSignal);

        if (response.ok) {
            await loadMessages(activeConversationId, fetchSignal);
        } else {
            const data = await response.json();
            const errorMsg = data.detail || 'Không thể tạo lại câu trả lời.';
            showChatAlert(errorMsg, 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Regenerate/Generation stopped by user.');
        } else {
            console.error('Lỗi tạo lại tin nhắn:', error);
            showChatAlert('Lỗi kết nối máy chủ.', 'error');
        }
    } finally {
        typingIndicator.classList.add('d-none');
        if (btnStop) btnStop.classList.add('d-none');
        currentAbortController = null;
        scrollToBottom();
    }
}

export function appendActionButtons(bubble, msg, isLast) {
    // 1. Add Copy code button to pre/code blocks
    const preElements = bubble.querySelectorAll('pre');
    preElements.forEach((pre) => {
        pre.style.position = 'relative';

        const copyBtn = document.createElement('button');
        copyBtn.type = 'button';
        copyBtn.className = 'btn btn-sm btn-outline-secondary position-absolute border-0 text-secondary opacity-75';
        copyBtn.style.top = '6px';
        copyBtn.style.right = '6px';
        copyBtn.style.fontSize = '0.7rem';
        copyBtn.style.padding = '2px 6px';
        copyBtn.style.backgroundColor = 'rgba(15, 22, 38, 0.6)';
        copyBtn.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy';

        copyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const codeText = pre.querySelector('code')?.innerText || pre.innerText;
            navigator.clipboard.writeText(codeText).then(() => {
                copyBtn.innerHTML = '<i class="bi bi-check-lg text-success me-1"></i>Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy';
                }, 2000);
            });
        });
        pre.appendChild(copyBtn);
    });

    // 2. Action bar at bottom of assistant bubble
    const actionBar = document.createElement('div');
    actionBar.className = 'd-flex gap-3 mt-3 pt-2 border-top border-secondary border-opacity-5 justify-content-end align-items-center opacity-75';
    actionBar.style.fontSize = '0.75rem';

    // Copy All Button
    const copyAllBtn = document.createElement('button');
    copyAllBtn.type = 'button';
    copyAllBtn.className = 'btn btn-link p-0 text-secondary text-decoration-none d-flex align-items-center gap-1';
    copyAllBtn.innerHTML = '<i class="bi bi-copy"></i><span>Sao chép</span>';
    copyAllBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(msg.content).then(() => {
            copyAllBtn.innerHTML = '<i class="bi bi-check-lg text-success"></i><span class="text-success">Đã sao chép</span>';
            setTimeout(() => {
                copyAllBtn.innerHTML = '<i class="bi bi-copy"></i><span>Sao chép</span>';
            }, 2000);
        });
    });
    actionBar.appendChild(copyAllBtn);

    // Regenerate Button (only if last message is from assistant)
    if (isLast) {
        const regenBtn = document.createElement('button');
        regenBtn.type = 'button';
        regenBtn.className = 'btn btn-link p-0 text-info text-decoration-none d-flex align-items-center gap-1';
        regenBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i><span>Tạo lại</span>';
        regenBtn.addEventListener('click', () => {
            regenerateResponse();
        });
        actionBar.appendChild(regenBtn);
    }

    bubble.appendChild(actionBar);
}

// Render Messages list inside screen
export function renderMessages(messages) {
    const messagesBox = document.getElementById("messagesBox");
    if (!messagesBox) return;

    // 1. Clear MathJax's internal tracking BEFORE destroying DOM nodes
    if (window.MathJax && typeof window.MathJax.typesetClear === 'function') {
        try { window.MathJax.typesetClear(); } catch (e) { /* ignore */ }
    }

    messagesBox.innerHTML = '';

    if (messages.length === 0) {
        messagesBox.innerHTML = `
            <div class="text-center py-5 text-secondary opacity-50 small">
                Bắt đầu gửi tin nhắn để trò chuyện với Trợ lý AI.
            </div>
        `;
        return;
    }

    messages.forEach((msg, index) => {
        const isUser = msg.role === 'user';
        const isLast = index === messages.length - 1;
        const outerDiv = document.createElement('div');
        outerDiv.className = `d-flex w-100 ${isUser ? 'justify-content-end' : 'justify-content-start'}`;

        const bubble = document.createElement('div');
        bubble.className = `msg-bubble ${isUser ? 'msg-user' : 'msg-model'}`;

        if (isUser) {
            bubble.innerText = msg.content;
        } else {
            // Use content_html pre-rendered from Python backend
            bubble.innerHTML = msg.content_html || msg.content;

            // Scan for mermaid code blocks
            processMermaidCodeBlocks(bubble);

            // Append action buttons (Copy code, Copy all, Regenerate)
            appendActionButtons(bubble, msg, isLast);
        }

        outerDiv.appendChild(bubble);
        messagesBox.appendChild(outerDiv);
    });

    // 2. Render mathematical formulas with MathJax
    //    Chain through startup.promise so each call waits for the previous to finish
    if (window.MathJax && window.MathJax.startup) {
        window.MathJax.startup.promise = window.MathJax.startup.promise
            .then(() => {
                window.MathJax.typesetClear();
                return window.MathJax.typesetPromise();
            })
            .catch((err) => {
                console.error("MathJax typesetting error:", err);
            });
    }

    scrollToBottom();
}

// Process Mermaid code blocks to render visual charts
export function processMermaidCodeBlocks(element) {
    const preElements = element.querySelectorAll('pre');
    preElements.forEach((pre, index) => {
        const code = pre.querySelector('code');
        if (code && (code.className.includes('language-mermaid') || code.innerText.trim().startsWith('graph') || code.innerText.trim().startsWith('sequenceDiagram'))) {
            const rawMermaidCode = code.innerText.trim();

            // Create unique ID for rendering
            const uniqueId = `mermaid-chart-${Date.now()}-${index}`;

            // Create container to render diagram
            const mermaidContainer = document.createElement('div');
            mermaidContainer.className = 'mermaid-container';
            mermaidContainer.innerHTML = `<div class="mermaid" id="${uniqueId}">${escapeHtml(rawMermaidCode)}</div>`;

            // Replace pre block with mermaid container
            pre.parentNode.replaceChild(mermaidContainer, pre);

            // Dynamic rendering with mermaid
            if (window.mermaid) {
                try {
                    window.mermaid.run({
                        nodes: mermaidContainer.querySelectorAll('.mermaid')
                    });
                } catch (e) {
                    console.error('Lỗi render Mermaid:', e);
                }
            }
        }
    });
}

// Send Message Trigger
export async function sendMessage(event, signal) {
    if (event) event.preventDefault();
    document.getElementById('chatAlertBox').classList.add('d-none');

    const chatInput = document.getElementById("chatInput");
    if (!chatInput) return;
    const messageText = chatInput.value.trim();
    if (!messageText || !activeConversationId) return;

    const token = getToken();
    const messagesBox = document.getElementById("messagesBox");
    const typingIndicator = document.getElementById("typingIndicator");
    const btnStop = document.getElementById("btnStopGenerating");

    // 1. Clear input field immediately
    chatInput.value = '';

    // 2. Append User message locally in UI
    const userDiv = document.createElement('div');
    userDiv.className = 'd-flex w-100 justify-content-end';
    const userBubble = document.createElement('div');
    userBubble.className = 'msg-bubble msg-user';
    userBubble.innerText = messageText;
    userDiv.appendChild(userBubble);
    messagesBox.appendChild(userDiv);

    // Scroll down
    scrollToBottom();

    // 3. Show typing indicator and stop generating button
    typingIndicator.classList.remove('d-none');
    if (btnStop) btnStop.classList.remove('d-none');

    currentAbortController = new AbortController();
    const fetchSignal = signal || currentAbortController.signal;

    try {
        const response = await api.sendMessage(token, activeConversationId, messageText, fetchSignal);
        const data = await response.json();

        if (response.ok) {
            // Reload messages to get updated token counts and proper rendering
            await loadMessages(activeConversationId, fetchSignal);

            // If it was the first message, conversation title has updated, reload list
            const activeItem = conversations.find(c => c.id === activeConversationId);
            if (activeItem && activeItem.title === "Cuộc trò chuyện mới") {
                await loadConversations(fetchSignal);
                // Select item in list
                const updatedItem = conversations.find(c => c.id === activeConversationId);
                if (updatedItem) {
                    document.getElementById('activeChatTitle').innerText = updatedItem.title;
                }
            }
        } else {
            const errorMsg = data.detail || 'Không gửi được tin nhắn.';
            showChatAlert(errorMsg, 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Generation stopped by user.');
        } else {
            console.error('Lỗi gửi tin nhắn:', error);
            showChatAlert('Lỗi kết nối máy chủ.', 'error');
        }
    } finally {
        typingIndicator.classList.add('d-none');
        if (btnStop) btnStop.classList.add('d-none');
        currentAbortController = null;
        scrollToBottom();
    }
}

// Quick Suggestion Trigger
export async function startQuickChat(promptText, signal) {
    document.getElementById('chatAlertBox').classList.add('d-none');
    const token = getToken();

    currentAbortController = new AbortController();
    const fetchSignal = signal || currentAbortController.signal;

    try {
        const response = await api.createConversation(token, fetchSignal);

        if (response.ok) {
            const newConv = await response.json();
            setActiveConversationId(newConv.id);

            await loadConversations(fetchSignal);
            await selectConversation(newConv.id, fetchSignal);

            // Put text into input field and submit it
            const chatInput = document.getElementById("chatInput");
            if (chatInput) {
                chatInput.value = promptText;
            }
            await sendMessage(null, fetchSignal);
        } else {
            showChatAlert('Không thể tạo cuộc trò chuyện mới.', 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Lỗi khi tạo cuộc trò chuyện:', error);
        showChatAlert('Lỗi kết nối máy chủ.', 'error');
    }
}

// Scroll chat panel to bottom
export function scrollToBottom() {
    const container = document.getElementById("messagesBox");
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Scroll chat panel to bottom smoothly
export function scrollToBottomSmooth() {
    const container = document.getElementById("messagesBox");
    if (container) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// Global JavaScript Error Logger
window.onerror = function(message, source, lineno, colno, error) {
    api.logBrowserError({
        message: message,
        source: source,
        lineno: lineno,
        colno: colno,
        stack: error ? error.stack : ''
    }).catch(e => console.error('Failed to log error to server:', e));
    return false;
};

window.onunhandledrejection = function(event) {
    const error = event.reason;
    api.logBrowserError({
        message: 'Unhandled Promise Rejection: ' + (error ? error.message || error : 'unknown'),
        source: '',
        lineno: 0,
        colno: 0,
        stack: error ? error.stack : ''
    }).catch(e => console.error('Failed to log rejection to server:', e));
};

// Page Load Initialization
document.addEventListener("DOMContentLoaded", () => {
    // Enforce authentication
    checkAuth(true);

    // Initial loading of conversation list
    loadConversations();

    // Handle submit via enter key
    const chatInput = document.getElementById("chatInput");
    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

// EXPOSE TO GLOBAL WINDOW SCOPE FOR HTML ONCLICK EVENT HANDLERS
window.createNewConversation = () => createNewConversation();
window.selectConversation = (convId) => selectConversation(convId);
window.deleteConversation = (event, convId) => deleteConversation(event, convId);
window.stopGenerating = () => stopGenerating();
window.regenerateResponse = () => regenerateResponse();
window.sendMessage = (event) => sendMessage(event);
window.startQuickChat = (promptText) => startQuickChat(promptText);
