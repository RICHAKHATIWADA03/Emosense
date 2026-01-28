"""Subscription management page"""
import streamlit as st
from datetime import datetime
from database import upgrade_to_premium, record_payment
import config

def show_subscription_page():
    """Display subscription management page"""
    st.title("💎 Subscription Plans")
    
    user = st.session_state.user
    current_tier = user.get('subscription_tier', 'free')
    
    # Show current plan
    st.subheader("Your Current Plan")
    
    if current_tier == 'free':
        st.info("🆓 **Free Plan** - You're currently on the free plan")
    else:
        expiry = user.get('subscription_end')
        if expiry:
            expiry_date = datetime.fromisoformat(expiry)
            days_left = (expiry_date - datetime.now()).days
            st.success(f"⭐ **Premium Plan** - Active until {expiry_date.strftime('%B %d, %Y')} ({days_left} days left)")
        else:
            st.success("⭐ **Premium Plan** - Active")
    
    st.markdown("---")
    
    # Show plan comparison
    st.subheader("Compare Plans")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 𝓯𝓻𝓮𝓮 Plan
        **$0/month**

        ☑️ Recording up to **30 seconds**\n
        ☑️ Upload files up to **50 MB**\n
        ☑️ Last **10 analyses** saved\n
        ☑️ Basic emotion detection\n
        ☑️ PDF reports\n
        🔒 Advanced metrics\n
        🔒 Priority processing\n
        🔒 Personalized recommendations
        """)
        
        if current_tier == 'free':
            st.button("Current Plan", disabled=True, key="free_current")
    
    with col2:
        st.markdown("""
        ### ⭐ Premium Plan
        **$9.99/month**
        
        ☑️ Recording up to **2 minutes**  
        ☑️ Upload files up to **500 MB**  
        ☑️ **Unlimited** analysis history  
        ☑️ Advanced emotion detection  
        ☑️ PDF reports  
        ☑️ **Advanced performance metrics**  
        ☑️ **Priority processing**  
        ☑️ **Personalized recommendations**  
        """)
        
        if current_tier == 'free':
            if st.button("⏫ Upgrade to Premium", type="primary", key="upgrade_btn"):
                st.session_state.show_payment = True
        else:
            st.button("Current Plan", disabled=True, key="premium_current")
    
    # Payment section (not inside form anymore)
    if st.session_state.get('show_payment', False):
        st.markdown("---")
        st.subheader("💳 Upgrade to Premium")
        
        st.info("**Demo Mode:** Enter any card details to simulate payment")
        
        # Payment form
        with st.form("payment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                card_number = st.text_input("Card Number", placeholder="1234 5678 9012 3456")
                card_name = st.text_input("Cardholder Name", placeholder="John Doe")
            
            with col2:
                expiry = st.text_input("Expiry Date (MM/YY)", placeholder="12/25")
                cvv = st.text_input("CVV", type="password", placeholder="123")
            
            agree = st.checkbox("I agree to the terms and conditions")
            
            submitted = st.form_submit_button("💳 Pay $9.99", type="primary")
        
        # Handle submission outside the form
        if submitted:
            if not agree:
                st.error("Please agree to the terms and conditions")
            elif card_number and card_name and expiry and cvv:
                # Simulate payment processing
                with st.spinner("Processing payment..."):
                    import time
                    time.sleep(2)
                    
                    # Upgrade user
                    upgrade_to_premium(user['id'], duration_days=30)
                    
                    # Record payment
                    record_payment(
                        user['id'],
                        9.99,
                        'card',
                        f'txn_{int(time.time())}'
                    )
                    
                    # Update session
                    st.session_state.user['subscription_tier'] = 'premium'
                    st.session_state.show_payment = False
                    
                    st.success("🎉 Payment successful! You are now a Premium member!")
                    st.balloons()
                    
                    # Refresh after showing success
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Please fill in all payment details")
        
        # Cancel button outside form
        if st.button("Cancel Payment"):
            st.session_state.show_payment = False
            st.rerun()
    
    st.markdown("---")
    
    # Usage statistics
    st.subheader("Your Overall Usage")
    
    from database import get_user_stats
    stats = get_user_stats(user['id'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if current_tier == 'free':
            st.metric("Analyses Saved", f"{stats['total_analyses']}/10")
            if stats['total_analyses'] >= 10:
                st.warning("SORRY, Limit reached!")
        else:
            st.metric("Analyses Saved", stats['total_analyses'])
    
    with col2:
        st.metric("Total Duration", f"{stats['total_duration']:.1f}s")
    
    with col3:
        st.metric("Avg Confidence", f"{stats['average_confidence']:.1%}")
    
    # Show feature comparison
    if current_tier == 'free':
        st.markdown("---")
        st.info("💡 **Tip:** Upgrade to Premium to unlock unlimited analyses and advanced metrics!")
