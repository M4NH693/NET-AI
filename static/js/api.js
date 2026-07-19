/**
 * api.js - Core API communication layer with AbortController signal support.
 */

export async function listConversations(token, signal) {
    return await fetch('/api/chat/conversations', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        signal
    });
}

export async function createConversation(token, signal) {
    return await fetch('/api/chat/conversations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: "Cuộc trò chuyện mới" }),
        signal
    });
}

export async function deleteConversation(token, convId, signal) {
    return await fetch(`/api/chat/conversations/${convId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        signal
    });
}

export async function listMessages(token, convId, signal) {
    return await fetch(`/api/chat/conversations/${convId}/messages`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        signal
    });
}

export async function sendMessage(token, convId, content, signal) {
    return await fetch(`/api/chat/conversations/${convId}/messages`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content }),
        signal
    });
}

export async function regenerateResponse(token, convId, signal) {
    return await fetch(`/api/chat/conversations/${convId}/regenerate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        signal
    });
}

export async function logBrowserError(payload, signal) {
    return await fetch('/api/debug/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal
    });
}
