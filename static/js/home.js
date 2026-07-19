async function initPage() {
    // Restore AbortController signal support to home getCurrentUser fetch call if passed
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;

    const user = await getCurrentUser(signal);
    const heroTitle = document.getElementById('heroTitle');
    const heroDesc = document.getElementById('heroDesc');
    const heroActions = document.getElementById('heroActions');

    if (user) {
        // Render authenticated UI
        const displayName = user.full_name || user.username;
        heroTitle.innerHTML = `Chào mừng trở lại, <span class="logo-text">${escapeHtml(displayName)}</span>!`;
        heroDesc.innerText = 'Tài khoản của bạn đã được xác thực thành công qua JWT Token (LocalStorage). Đây là khu vực trang chủ trống của bạn. Bạn có thể bắt đầu xây dựng nội dung ngay tại đây.';

        heroActions.innerHTML = `
            <a href="/account" class="btn btn-premium px-4 py-2-5">
                <i class="bi bi-gear-fill me-2"></i>Quản lý tài khoản
            </a>
            <button class="btn btn-outline-premium px-4 py-2-5" onclick="logout()">
                <i class="bi bi-box-arrow-right me-2"></i>Đăng xuất
            </button>
        `;
    } else {
        // Render guest UI
        heroTitle.innerHTML = `Khám phá <span class="logo-text">NetAI Portal</span>`;
        heroDesc.innerText = 'Hệ thống cổng thông tin tích hợp xác thực JWT bảo mật cao. Hãy đăng ký một tài khoản mới để trải nghiệm các dịch vụ của chúng tôi.';

        heroActions.innerHTML = `
            <a href="/register" class="btn btn-premium px-4 py-2-5">
                <i class="bi bi-person-plus-fill me-2"></i>Đăng ký tài khoản mới
            </a>
            <a href="/login" class="btn btn-outline-premium px-4 py-2-5">
                <i class="bi bi-box-arrow-in-right me-2"></i>Đăng nhập ngay
            </a>
        `;
    }
}

// Run initialization
initPage();
