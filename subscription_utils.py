"""Utility functions for subscription management"""
import streamlit as st
import config

def get_user_limits():
    """Get limits based on user's subscription tier"""
    tier = st.session_state.user.get('subscription_tier', 'free')
    return config.SUBSCRIPTION_TIERS[tier]

def check_recording_limit(duration):
    """Check if recording duration is within limit"""
    limits = get_user_limits()
    return duration <= limits['max_recording_duration']

def check_upload_limit(file_size_mb):
    """Check if file size is within limit"""
    limits = get_user_limits()
    return file_size_mb <= limits['max_upload_size_mb']

def check_history_limit():
    """Check if user can save more analyses"""
    from database import check_subscription_limits
    can_save, reason = check_subscription_limits(st.session_state.user['id'])
    return can_save

def show_upgrade_prompt(reason='general'):
    """Show upgrade prompt"""
    limits = get_user_limits()
    
    if reason == 'recording':
        st.warning(f"⏱️ **Free users are limited to {limits['max_recording_duration']} seconds**")
        st.info("⏫ Upgrade to Premium to record up to 2 minutes!")
    elif reason == 'upload':
        st.warning(f"📁 **Free users are limited to {limits['max_upload_size_mb']} MB files**")
        st.info("⏫ Upgrade to Premium to upload files up to 500 MB!")
    elif reason == 'history':
        st.warning(f"💾 **Free users can save only {limits['max_history']} analyses**")
        st.info("⏫ Upgrade to Premium for unlimited history!")
    
    if st.button("💎 View Premium Plans"):
        st.session_state.page = "💎 Subscription"
        st.rerun()
