// Toggle between signin and signup forms
document.addEventListener('DOMContentLoaded', function() {
    const showSignup = document.getElementById('showSignup');
    const showSignin = document.getElementById('showSignin');
    const signinForm = document.getElementById('signinForm');
    const signupForm = document.getElementById('signupForm');
    
    if (showSignup && showSignin) {
        showSignup.addEventListener('click', function(e) {
            e.preventDefault();
            signinForm.classList.remove('auth-form-active');
            signinForm.style.opacity = '0';
            signinForm.style.transform = 'translateX(-100%)';
            
            signupForm.classList.add('auth-form-active');
            signupForm.style.opacity = '1';
            signupForm.style.transform = 'translateX(0)';
        });
        
        showSignin.addEventListener('click', function(e) {
            e.preventDefault();
            signupForm.classList.remove('auth-form-active');
            signupForm.style.opacity = '0';
            signupForm.style.transform = 'translateX(100%)';
            
            signinForm.classList.add('auth-form-active');
            signinForm.style.opacity = '1';
            signinForm.style.transform = 'translateX(0)';
        });
    }
    
    // Initialize carousel
    const myCarousel = document.querySelector('#medicalCarousel');
    if (myCarousel) {
        const carousel = new bootstrap.Carousel(myCarousel, {
            interval: 5000,
            pause: 'hover'
        });
    }
    
    // Handle image upload preview
    const patientImageInput = document.getElementById('patientImage');
    if (patientImageInput) {
        patientImageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    // You can add a preview functionality here if needed
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Form validation for signup
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const password = document.getElementById('signupPassword').value;
            const confirmPassword = document.getElementById('signupConfirmPassword').value;
            
            if (password !== confirmPassword) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }
});