"""Authentication module for Streamlit"""
import streamlit as st
from database import create_user, verify_user

def check_authentication():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
    return st.session_state.authenticated

def login_page():
    """Display login page"""
    st.title("🎭 EmoSense - Login")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back!")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if username and password:
                success, user = verify_user(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Sign Up", type="primary"):
            if not all([new_username, new_email, new_password, confirm_password]):
                st.warning("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                success, result = create_user(new_username, new_email, new_password)
                if success:
                    st.success("Account created successfully! Please login.")
                else:
                    st.error(f"Failed to create account: {result}")

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()
