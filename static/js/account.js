let currentUser = null;

async function loadProfile() {
    // Require authentication, redirect to login if not logged in
    // Restore AbortController signal support to checkAuth fetch call if passed
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;

    currentUser = await checkAuth(true, signal);
    if (!currentUser) return;

    // Populate read-only fields
    document.getElementById('usernameText').innerText = currentUser.username;
    document.getElementById('emailText').innerText = currentUser.email;

    // Populate avatar preview
    const avatarUrl = currentUser.avatar_url ? `/media/profile_pics/${currentUser.avatar_url}` : '/static/profile_pics/default.jpg';
    document.getElementById('avatarPreview').src = avatarUrl;

    // Formatted joined date
    if (currentUser.created_at) {
        const date = new Date(currentUser.created_at);
        document.getElementById('joinedDateText').innerText = date.toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Populate inputs
    document.getElementById('fullNameInput').value = currentUser.full_name || '';
}

async function uploadAvatarFile(input) {
    if (!input.files || !input.files[0]) return;
    
    const file = input.files[0];
    const alertBox = document.getElementById('alertBox');
    const spinner = document.getElementById('avatarSpinner');
    
    // Hide previous alert
    alertBox.classList.add('d-none');
    alertBox.className = 'alert alert-custom';
    
    // Show loading spinner overlay
    spinner.classList.remove('d-none');
    
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);
    
    // Restore AbortController signal support to avatar upload fetch call
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;
    
    try {
        const response = await fetch('/api/auth/avatar', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData,
            signal: signal
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Cập nhật ảnh đại diện thành công!', 'success');
            currentUser = data;
            
            // Update avatar preview
            const newAvatarUrl = data.avatar_url ? `/media/profile_pics/${data.avatar_url}` : '/static/profile_pics/default.jpg';
            document.getElementById('avatarPreview').src = newAvatarUrl;
            
            // Update navigation bar
            updateNavbar();
        } else {
            const errorMsg = data.detail || 'Không thể tải ảnh đại diện lên.';
            showAlert(errorMsg, 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Avatar upload aborted');
        } else {
            console.error('Lỗi khi tải ảnh:', error);
            showAlert('Lỗi kết nối đến máy chủ. Vui lòng thử lại sau.', 'error');
        }
    } finally {
        spinner.classList.add('d-none');
        // Reset input value to allow uploading same file again
        input.value = '';
    }
}

async function submitUpdateProfile(event) {
    event.preventDefault();

    const alertBox = document.getElementById('alertBox');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnSpinner = document.getElementById('btnSpinner');

    const fullName = document.getElementById('fullNameInput').value.trim();
    const password = document.getElementById('passwordInput').value;
    const confirmPassword = document.getElementById('confirmPasswordInput').value;

    // Hide alert
    alertBox.classList.add('d-none');
    alertBox.className = 'alert alert-custom';

    // Password confirmation check
    if (password) {
        if (password !== confirmPassword) {
            showAlert('Mật khẩu mới và xác nhận mật khẩu mới không trùng khớp.', 'error');
            return;
        }
    }

    // Show loading state
    btnSubmit.disabled = true;
    btnSpinner.classList.remove('d-none');

    const token = getToken();
    const bodyData = {
        full_name: fullName || null
    };

    if (password) {
        bodyData.password = password;
    }

    // Restore AbortController signal support to update profile fetch call
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;

    try {
        const response = await fetch('/api/auth/me', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(bodyData),
            signal: signal
        });

        const data = await response.json();

        if (response.ok) {
            showAlert('Cập nhật thông tin tài khoản thành công!', 'success');
            currentUser = data;

            // Clear password fields
            document.getElementById('passwordInput').value = '';
            document.getElementById('confirmPasswordInput').value = '';

            // Update global navbar
            updateNavbar();
        } else {
            const errorDetail = data.detail || 'Không thể cập nhật thông tin. Vui lòng kiểm tra lại.';
            showAlert(errorDetail, 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Update profile aborted');
        } else {
            console.error('Lỗi khi cập nhật:', error);
            showAlert('Lỗi kết nối đến máy chủ. Vui lòng thử lại sau.', 'error');
        }
    } finally {
        btnSubmit.disabled = false;
        btnSpinner.classList.add('d-none');
    }
}

function showAlert(message, type) {
    const alertBox = document.getElementById('alertBox');
    const alertIcon = document.getElementById('alertIcon');
    const alertMessage = document.getElementById('alertMessage');

    alertMessage.innerHTML = message;
    alertBox.classList.remove('d-none');

    if (type === 'success') {
        alertBox.classList.add('alert-success');
        alertIcon.className = 'bi bi-check-circle-fill text-success';
    } else {
        alertBox.classList.add('alert-danger');
        alertIcon.className = 'bi bi-exclamation-triangle-fill text-danger';
    }
}

// Load profile on page load
loadProfile();
