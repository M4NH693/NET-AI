// Guest-only page check
checkAuth(false);

let savedEmail = '';

// Handle Step 1: Send OTP to Email
async function submitSendOTP(event) {
    event.preventDefault();
    
    const alertBox = document.getElementById('alertBox');
    const btnSendOTP = document.getElementById('btnSendOTP');
    const btnSpinner1 = document.getElementById('btnSpinner1');
    const email = document.getElementById('emailInput').value.trim();
    
    // Hide previous alert
    alertBox.classList.add('d-none');
    alertBox.className = 'alert alert-custom';
    
    // Show loading state
    btnSendOTP.disabled = true;
    btnSpinner1.classList.remove('d-none');
    
    // Restore AbortController signal support to forgot password fetch call
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;
    
    try {
        const response = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email }),
            signal: signal
        });
        
        const data = await response.json();
        
        if (response.ok) {
            savedEmail = email;
            showAlert('Mã OTP đã được gửi thành công! Vui lòng kiểm tra email của bạn.', 'success');
            
            // Transition to Step 2
            setTimeout(() => {
                alertBox.classList.add('d-none');
                document.getElementById('step1Form').classList.add('d-none');
                document.getElementById('step2Form').classList.remove('d-none');
                document.getElementById('emailDisplay').innerText = email;
                
                document.getElementById('pageTitle').innerText = 'Nhập mã xác thực';
                document.getElementById('pageSubtitle').innerText = 'Mã OTP 4 số đã được gửi qua email. Vui lòng nhập mã và đặt mật khẩu mới.';
            }, 1500);
        } else {
            const errorDetail = data.detail || 'Không thể gửi mã xác thực. Vui lòng kiểm tra lại.';
            showAlert(errorDetail, 'error');
            btnSendOTP.disabled = false;
            btnSpinner1.classList.add('d-none');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Send OTP fetch aborted');
        } else {
            console.error('Lỗi gửi OTP:', error);
            showAlert('Lỗi kết nối đến máy chủ. Vui lòng thử lại sau.', 'error');
            btnSendOTP.disabled = false;
            btnSpinner1.classList.add('d-none');
        }
    }
}

// Handle Step 2: Verify OTP and Reset Password
async function submitResetPassword(event) {
    event.preventDefault();
    
    const alertBox = document.getElementById('alertBox');
    const btnResetPassword = document.getElementById('btnResetPassword');
    const btnSpinner2 = document.getElementById('btnSpinner2');
    
    const otpCode = document.getElementById('otpInput').value.trim();
    const password = document.getElementById('passwordInput').value;
    const confirmPassword = document.getElementById('confirmPasswordInput').value;
    
    // Hide previous alert
    alertBox.classList.add('d-none');
    alertBox.className = 'alert alert-custom';
    
    if (password !== confirmPassword) {
        showAlert('Mật khẩu và xác nhận mật khẩu không trùng khớp.', 'error');
        return;
    }
    
    // Show loading state
    btnResetPassword.disabled = true;
    btnSpinner2.classList.remove('d-none');
    
    // Restore AbortController signal support to reset password fetch call
    const currentAbortController = new AbortController();
    const { signal } = currentAbortController;
    
    try {
        const response = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: savedEmail,
                otp_code: otpCode,
                password: password
            }),
            signal: signal
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Đặt lại mật khẩu thành công! Đang chuyển hướng về trang đăng nhập...', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            const errorDetail = data.detail || 'Đặt lại mật khẩu thất bại. Vui lòng thử lại.';
            showAlert(errorDetail, 'error');
            btnResetPassword.disabled = false;
            btnSpinner2.classList.add('d-none');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('Reset password fetch aborted');
        } else {
            console.error('Lỗi đặt lại mật khẩu:', error);
            showAlert('Lỗi kết nối đến máy chủ. Vui lòng thử lại sau.', 'error');
            btnResetPassword.disabled = false;
            btnSpinner2.classList.add('d-none');
        }
    }
}

function backToStep1() {
    document.getElementById('step2Form').classList.add('d-none');
    document.getElementById('step1Form').classList.remove('d-none');
    document.getElementById('btnSendOTP').disabled = false;
    document.getElementById('btnSpinner1').classList.add('d-none');
    document.getElementById('alertBox').classList.add('d-none');
    
    document.getElementById('pageTitle').innerText = 'Khôi phục mật khẩu';
    document.getElementById('pageSubtitle').innerText = 'Vui lòng nhập email của bạn để nhận mã xác thực OTP 4 số';
    
    document.getElementById('otpInput').value = '';
    document.getElementById('passwordInput').value = '';
    document.getElementById('confirmPasswordInput').value = '';
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
