// Guest-only page check
checkAuth(false);

async function submitRegister(event) {
    event.preventDefault();

    const alertBox = document.getElementById('alertBox');
    const alertIcon = document.getElementById('alertIcon');
    const alertMessage = document.getElementById('alertMessage');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnSpinner = document.getElementById('btnSpinner');

    // Form inputs
    const fullName = document.getElementById('fullNameInput').value.trim();
    const username = document.getElementById('usernameInput').value.trim();
    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passwordInput').value;
    const confirmPassword = document.getElementById('confirmPasswordInput').value;

    // Hide previous alert
    alertBox.classList.add('d-none');
    alertBox.className = 'alert alert-custom';

    // Client-side passwords match check
    if (password !== confirmPassword) {
        showAlert('Mật khẩu và xác nhận mật khẩu không trùng khớp.', 'error');
        return;
    }

    // Show loading state
    btnSubmit.disabled = true;
    btnSpinner.classList.remove('d-none');

    // Restore AbortController signal support to register fetch call
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName || null,
                username: username,
                email: email,
                password: password
            }),
            signal: signal
        });

        const data = await response.json();

        if (response.ok) {
            showAlert('Đăng ký tài khoản thành công! Đang chuyển hướng đến trang đăng nhập...', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            // If validation or error details are returned
            const errorDetail = data.detail;
            let errorMsg = 'Đã có lỗi xảy ra. Vui lòng kiểm tra lại.';

            if (typeof errorDetail === 'string') {
                errorMsg = errorDetail;
            } else if (Array.isArray(errorDetail)) {
                errorMsg = errorDetail.map(err => `${err.loc.join('.')}: ${err.msg}`).join('<br>');
            }

            showAlert(errorMsg, 'error');
            btnSubmit.disabled = false;
            btnSpinner.classList.add('d-none');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Register fetch aborted');
        } else {
            console.error('Lỗi kết nối:', error);
            showAlert('Không thể kết nối đến máy chủ. Vui lòng thử lại sau.', 'error');
            btnSubmit.disabled = false;
            btnSpinner.classList.add('d-none');
        }
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
