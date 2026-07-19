import * as api from './api.js';
import { loadMessages } from './chat.js';

export let conversations = [];
export let activeConversationId = null;

export function setActiveConversationId(id) {
    activeConversationId = id;
}

export function setConversations(list) {
    conversations = list;
}

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
function showChatAlert(message, type) {
    const alertBox = document.getElementById('chatAlertBox');
    const alertIcon = document.getElementById('chatAlertIcon');
    const alertMessage = document.getElementById('chatAlertMessage');
    
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

// Fetch and Load conversations list from API
export async function loadConversations(signal) {
    const token = getToken();
    try {
        const response = await api.listConversations(token, signal);
        if (response.ok) {
            conversations = await response.json();
            renderConversations();
        } else {
            showChatAlert('Không thể tải lịch sử cuộc trò chuyện.', 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Lỗi khi tải danh sách hội thoại:', error);
        showChatAlert('Lỗi kết nối đến máy chủ.', 'error');
    }
}

// Render Conversations list UI
export function renderConversations() {
    const listContainer = document.getElementById("conversationsList");
    if (!listContainer) return;
    listContainer.innerHTML = '';
    
    if (conversations.length === 0) {
        listContainer.innerHTML = `
            <div class="text-center py-4 text-secondary opacity-50 small">
                Chưa có cuộc trò chuyện nào.
            </div>
        `;
        return;
    }
    
    conversations.forEach(conv => {
        const isActive = conv.id === activeConversationId;
        const item = document.createElement('div');
        item.className = `conversation-item p-3 mb-2 d-flex align-items-center justify-content-between ${isActive ? 'active' : ''}`;
        item.setAttribute('onclick', `selectConversation('${conv.id}')`);
        
        item.innerHTML = `
            <div class="d-flex align-items-center gap-2 text-truncate pe-2">
                <i class="bi ${isActive ? 'bi-chat-left-dots-fill text-info' : 'bi-chat-left text-secondary'}"></i>
                <span class="text-light small text-truncate fw-medium" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
            </div>
            <button onclick="deleteConversation(event, '${conv.id}')" class="btn btn-link text-secondary text-opacity-50 hover-text-danger p-0 d-flex align-items-center justify-content-center" style="width: 24px; height: 24px; border-radius: 4px;">
                <i class="bi bi-trash3-fill small"></i>
            </button>
        `;
        listContainer.appendChild(item);
    });
}

// Create New Conversation Session
export async function createNewConversation(signal) {
    document.getElementById('chatAlertBox').classList.add('d-none');
    const token = getToken();

    try {
        const response = await api.createConversation(token, signal);

        if (response.ok) {
            const newConv = await response.json();
            activeConversationId = newConv.id;

            await loadConversations(signal);
            await selectConversation(newConv.id, signal);
        } else {
            showChatAlert('Không thể tạo cuộc trò chuyện mới.', 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Lỗi khi tạo cuộc trò chuyện:', error);
        showChatAlert('Lỗi kết nối máy chủ.', 'error');
    }
}

// Select Active Conversation
export async function selectConversation(convId, signal) {
    activeConversationId = convId;

    const items = document.querySelectorAll('.conversation-item');
    items.forEach(item => item.classList.remove('active'));

    const activeItem = conversations.find(c => c.id === convId);
    if (activeItem) {
        document.getElementById('activeChatTitle').innerText = activeItem.title;
        renderConversations();
    }

    document.getElementById('welcomePanel').classList.add('d-none');
    document.getElementById('activeChatScreen').classList.remove('d-none');

    await loadMessages(convId, signal);
}

// Delete Conversation Session
export async function deleteConversation(event, convId, signal) {
    event.stopPropagation();

    const token = getToken();
    if (!confirm("Bạn có chắc chắn muốn xóa cuộc trò chuyện này?")) return;

    try {
        const response = await api.deleteConversation(token, convId, signal);

        if (response.status === 204) {
            if (activeConversationId === convId) {
                activeConversationId = null;
                document.getElementById('welcomePanel').classList.remove('d-none');
                document.getElementById('activeChatScreen').classList.add('d-none');
            }

            await loadConversations(signal);
        } else {
            showChatAlert('Xóa cuộc trò chuyện thất bại.', 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Lỗi khi xóa cuộc trò chuyện:', error);
        showChatAlert('Lỗi kết nối máy chủ.', 'error');
    }
}
