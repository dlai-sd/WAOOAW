"""
Google Sign-In Component for Reflex
Modal-based OAuth using Google Identity Services
"""

import reflex as rx
import os


def google_signin_modal(state_class, show_modal: str = "show_signin_modal") -> rx.Component:
    """
    Google Sign-In modal component
    
    Args:
        state_class: The state class that handles authentication
        show_modal: State variable name that controls modal visibility
        
    Returns:
        Reflex component for Google Sign-In modal
    """
    
    # Get Google Client ID from environment
    google_client_id = os.getenv('GOOGLE_CLIENT_ID', '987654321-abcdefghijk.apps.googleusercontent.com')
    
    return rx.cond(
        getattr(state_class, show_modal),
        # Modal overlay
        rx.box(
            # Modal container
            rx.box(
                # Close button
                rx.button(
                    "×",
                    on_click=lambda: setattr(state_class, show_modal, False),
                    position="absolute",
                    top="1rem",
                    right="1rem",
                    background="transparent",
                    border="none",
                    font_size="24px",
                    color="#5f6368",
                    cursor="pointer",
                    _hover={"color": "#3c4043"},
                ),
                
                # Modal header
                rx.box(
                    rx.heading("Sign in to Platform Portal", size="lg", margin_bottom="0.5rem"),
                    rx.text("Access internal operations dashboard", color="#5f6368", font_size="14px"),
                    text_align="center",
                    margin_bottom="1.5rem",
                ),
                
                # Google Sign-In button container
                rx.box(
                    # Google's button will be rendered here by JavaScript
                    rx.html(f"""
                        <div id="g_id_onload"
                             data-client_id="{google_client_id}"
                             data-callback="handleGoogleSignIn"
                             data-auto_prompt="false">
                        </div>
                        <div class="g_id_signin"
                             data-type="standard"
                             data-size="large"
                             data-theme="filled_black"
                             data-text="signin_with"
                             data-shape="rectangular"
                             data-logo_alignment="left"
                             data-width="280">
                        </div>
                    """),
                    display="flex",
                    justify_content="center",
                    align_items="center",
                ),
                
                # Loading state
                rx.cond(
                    state_class.is_authenticating,
                    rx.box(
                        rx.spinner(size="md", color="#4285F4"),
                        display="flex",
                        justify_content="center",
                        align_items="center",
                        padding="2rem",
                    ),
                ),
                
                # Error message
                rx.cond(
                    state_class.auth_error,
                    rx.box(
                        rx.text(state_class.auth_error, color="#c00", font_size="14px"),
                        background="#fee",
                        border="1px solid #fcc",
                        border_radius="8px",
                        padding="1rem",
                        margin_top="1rem",
                    ),
                ),
                
                # Modal styling
                background="#fff",
                border_radius="12px",
                padding="2rem",
                box_shadow="0 8px 32px rgba(0, 0, 0, 0.2)",
                max_width="400px",
                width="90%",
                position="relative",
                animation="slideUp 0.3s ease",
                on_click=lambda e: e.stop_propagation(),  # Prevent closing when clicking inside
            ),
            
            # Overlay styling
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            background="rgba(0, 0, 0, 0.5)",
            backdrop_filter="blur(4px)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="9999",
            animation="fadeIn 0.2s ease",
            on_click=lambda: setattr(state_class, show_modal, False),  # Close on overlay click
        ),
    )


def google_signin_script() -> rx.Component:
    """
    Script tags required for Google Identity Services
    Must be included in the page head
    """
    return rx.fragment(
        rx.script(src="https://accounts.google.com/gsi/client", defer=True),
        rx.script("""
            // Handle Google Sign-In callback
            window.handleGoogleSignIn = async function(response) {
                try {
                    const credential = response.credential;
                    
                    // Send token to backend for verification
                    const backendUrl = window.location.origin;
                    const verifyResponse = await fetch(`${backendUrl}/auth/google/verify`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ token: credential }),
                    });
                    
                    if (!verifyResponse.ok) {
                        throw new Error('Authentication failed');
                    }
                    
                    const userData = await verifyResponse.json();
                    
                    // Store token
                    localStorage.setItem('auth_token', userData.access_token);
                    localStorage.setItem('user_email', userData.email);
                    localStorage.setItem('user_name', userData.name);
                    localStorage.setItem('user_picture', userData.picture);
                    
                    // Trigger Reflex state update via event
                    // Reflex will pick this up and update state
                    const event = new CustomEvent('google-signin-success', {
                        detail: userData
                    });
                    window.dispatchEvent(event);
                    
                    // Reload page to refresh state
                    window.location.reload();
                    
                } catch (error) {
                    console.error('Google Sign-In error:', error);
                    const errorEvent = new CustomEvent('google-signin-error', {
                        detail: { error: error.message }
                    });
                    window.dispatchEvent(errorEvent);
                }
            };
            
            // CSS for animations
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        """),
    )


def google_signin_button(state_class) -> rx.Component:
    """
    Simple button that triggers the sign-in modal
    
    Args:
        state_class: The state class that handles modal visibility
        
    Returns:
        Sign-in button component
    """
    return rx.button(
        "Sign in with Google",
        on_click=lambda: setattr(state_class, "show_signin_modal", True),
        background="#4285F4",
        color="white",
        padding="0.75rem 1.5rem",
        border_radius="4px",
        border="none",
        font_size="14px",
        font_weight="500",
        cursor="pointer",
        _hover={"background": "#357ae8"},
        transition="background 0.2s ease",
    )
