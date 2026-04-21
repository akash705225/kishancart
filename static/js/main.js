// PlantNwelog — Main Frontend JavaScript

document.addEventListener("DOMContentLoaded", function() {

    // ═══════ PINCODE GATEWAY LOGIC ═══════
    const pincodeModal = document.getElementById("pincodeGatewayOverlay");
    
    // Check if the gateway exists on this page (Homepage only)
    if (pincodeModal) {
        // If already verified in this session, hide the overlay
        if (sessionStorage.getItem("serviceabilityVerified") === "true") {
            pincodeModal.style.display = "none";
            document.body.style.overflow = "auto";
        } else {
            // Prevent scrolling on background
            document.body.style.overflow = "hidden";
        }

        const gatewayForm = document.getElementById("pincodeGatewayForm");
        const errorToast = document.getElementById("pincodeErrorToast");
        const errorMessage = document.getElementById("pincodeErrorMsg");

        // Allowed pincodes (User requested)
        const allowedPincodes = ["274303", "274304", "274302", "274301", "845104"];

        gatewayForm.addEventListener("submit", function(e) {
            e.preventDefault();
            
            const name = document.getElementById("gatewayName").value.trim();
            const phone = document.getElementById("gatewayPhone").value.trim();
            const pincode = document.getElementById("gatewayPincode").value.trim();

            if (!name || !phone || !pincode) {
                showError("Please fill out all fields.");
                return;
            }

            // Check if pincode is valid
            if (allowedPincodes.includes(pincode)) {
                // Success! Unlock page
                sessionStorage.setItem("serviceabilityVerified", "true");
                
                // Optional: Save user data in session/local storage for later use
                localStorage.setItem("temp_user_name", name);
                localStorage.setItem("temp_user_phone", phone);
                localStorage.setItem("temp_user_pincode", pincode);

                // Hide Modal
                pincodeModal.style.opacity = "0";
                setTimeout(() => {
                    pincodeModal.style.display = "none";
                    document.body.style.overflow = "auto";
                }, 300);
            } else {
                // Invalid Pincode - Show error top right
                showError("Sorry, we do not deliver to " + pincode + " yet. Please try again.");
            }
        });

        function showError(msg) {
            errorMessage.textContent = msg;
            errorToast.classList.add("show");
            
            // Hide after 4 seconds
            setTimeout(() => {
                errorToast.classList.remove("show");
            }, 4000);
        }
    }

    // ═══════ MOBILE MENU ═══════
    const mobileToggle = document.getElementById("mobileToggle");
    const navLinks = document.getElementById("navLinks");
    
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener("click", function() {
            navLinks.classList.toggle("active");
            this.classList.toggle("open");
        });
    }

});

// Generic function for flash messages or toast handling...
function handleNewsletter(e) {
    e.preventDefault();
    alert("Thank you for subscribing!");
    e.target.reset();
}
