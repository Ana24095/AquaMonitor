import streamlit as st
import hashlib
import os

def hash_password(password):
    """Hash a password for storing."""
    salt = os.environ.get('PASSWORD_SALT', 'AquaNovaDefaultSalt')
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest()

def authenticate_user(username, password):
    """Verify username and password."""
    # In a real application, this would check against a database
    # For demo purposes, we're using a hardcoded credential set
    users = {
        'admin': hash_password('admin123'),
        'tech': hash_password('water2023'),
        'guest': hash_password('guest')
    }
    
    hashed_pw = hash_password(password)
    if username in users and users[username] == hashed_pw:
        return True
    return False

def render_login():
    """Render the login form."""
    # Removido el título para una interfaz más limpia
    
    # Create a centered login form with custom styling
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo primero y más grande (400px)
        try:
            st.image("new-logo.png", width=400)
        except:
            # Fallback for when the logo isn't available
            st.markdown("""
            <div style="text-align: center; margin: 20px 0; color: #0c6271; font-weight: bold; font-size: 1.8rem;">
                Environmental Monitoring
            </div>
            """, unsafe_allow_html=True)
            
        # Texto más pequeño debajo del logo (150px de ancho)
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); max-width: 150px; margin: 0 auto;">
            <h3 style="color: #0c6271; text-align: center; margin-bottom: 10px; font-size: 1.0rem;">Environmental Monitoring System</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)
        
        # Login form
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <small>Forgot password? Contact system administrator</small>
        </div>
        """, unsafe_allow_html=True)