/**
 * auth.js - Client-side authentication state manager
 */

const TOKEN_KEY = 'access_token';

// Retrieve token from local storage
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

// Save token to local storage
function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

// Remove token from local storage
function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
}

// Global logout handler
function logout() {
    removeToken();
    window.location.href = '/';
}

// Fetch current user from API
async function getCurrentUser() {
    const token = getToken();
    if (!token) return null;

    try {
        const response = await fetch('/api/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            return await response.json();
        } else {
            // Token expired or invalid
            removeToken();
            return null;
        }
    } catch (error) {
        console.error('Error fetching user:', error);
        return null;
    }
}

// Update the Navbar UI dynamically based on auth status
async function updateNavbar() {
    const navbarAuth = document.getElementById('navbarAuth');
    if (!navbarAuth) return;

    const user = await getCurrentUser();
    
    if (user) {
        // Logged in state
        const displayName = user.full_name || user.username;
        const avatarUrl = user.avatar_url ? `/media/profile_pics/${user.avatar_url}` : '/static/profile_pics/default.jpg';
        navbarAuth.innerHTML = `
            <div class="dropdown">
                <button class="btn btn-outline-premium dropdown-toggle d-flex align-items-center gap-2" type="button" id="userDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                    <img src="${avatarUrl}" alt="Avatar" class="rounded-circle" style="width: 24px; height: 24px; object-fit: cover;">
                    <span>${escapeHtml(displayName)}</span>
                </button>
                <ul class="dropdown-menu dropdown-menu-end dropdown-menu-dark glass-card animate slideIn" aria-labelledby="userDropdown" style="background: rgba(11, 15, 25, 0.95); border: 1px solid var(--border-color);">
                    <li><a class="dropdown-item py-2" href="/account"><i class="bi bi-gear-fill me-2"></i>Tài khoản</a></li>
                    <li><a class="dropdown-item py-2" href="/chat"><i class="bi bi-chat-left-dots-fill me-2"></i>Trợ lý AI</a></li>
                    <li><a class="dropdown-item py-2" href="/"><i class="bi bi-house-door me-2"></i>Trang chủ</a></li>
                    <li><hr class="dropdown-divider" style="background-color: var(--border-color);"></li>
                    <li>
                        <button class="dropdown-item text-danger py-2" onclick="logout()">
                            <i class="bi bi-box-arrow-right me-2"></i>Đăng xuất
                        </button>
                    </li>
                </ul>
            </div>
        `;
    } else {
        // Logged out state
        navbarAuth.innerHTML = `
            <a href="/login" class="btn btn-outline-premium px-3 py-2 text-decoration-none">Đăng nhập</a>
            <a href="/register" class="btn btn-premium px-3 py-2 text-decoration-none">Đăng ký</a>
        `;
    }
}

// Redirect if not authenticated (for protected pages)
async function checkAuth(protectedPage = true) {
    const user = await getCurrentUser();
    
    if (protectedPage && !user) {
        // Redirect to login if user is not logged in on a protected page
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
        return null;
    }
    
    if (!protectedPage && user) {
        // Redirect to home if user is logged in on guest pages (login/register)
        window.location.href = '/';
        return user;
    }
    
    return user;
}

// Helper to escape HTML tags to prevent XSS
function escapeHtml(string) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(string).replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Execute Navbar update automatically on page load
document.addEventListener('DOMContentLoaded', () => {
    updateNavbar();
});
