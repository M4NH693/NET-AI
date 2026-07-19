// Guest-only page check
checkAuth(false);

async function submitLogin(event) {
    event.preventDefault();

    const alertBox = document.getElementById('alertBox');
    const alertIcon = document.getElementById('alertIcon');
    const alertMessage = document.getElementById('alertMessage');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnSpinner = document.getElementById('btnSpinner');

    const email = document.getElementById('emailInput').value.trim();
    const password = document.getElementById('passwordInput').value;

    // Hide previous alert
    alertBox.classList.add('d-none');
    alertBox.className = 'alert alert-custom';

    // Show loading state
    btnSubmit.disabled = true;
    btnSpinner.classList.remove('d-none');

    // Restore AbortController signal support to login fetch call
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            }),
            signal: signal
        });

        const data = await response.json();

        if (response.ok) {
            // Save token to localStorage
            setToken(data.access_token);

            showAlert('Đăng nhập thành công! Đang chuyển hướng...', 'success');

            // Get redirect url from query parameter or default to Home
            const params = new URLSearchParams(window.location.search);
            const redirectUrl = params.get('redirect') || '/';

            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 1000);
        } else {
            const errorDetail = data.detail || 'Email hoặc mật khẩu không chính xác.';
            showAlert(errorDetail, 'error');
            btnSubmit.disabled = false;
            btnSpinner.classList.add('d-none');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Login fetch aborted');
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
