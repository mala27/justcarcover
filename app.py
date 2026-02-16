# Project Link: https://automatic-trout-6j56pqjx9vfxrr7-8501.app.github.dev/
# Version: v0.6 - MASTER (FIXED & AUDITED: Address + Crime + Test Drive + Decline)

import streamlit as st
import requests
import pandas as pd
import os
import time
from datetime import datetime

st.set_page_config(page_title="FairRate AI v0.6", layout="centered")
st.title("🚗 FairRate AI | v0.6 Master Engine")

# --- 1) IDENTITY & POSTCODE ---
col_a, col_b = st.columns(2)
with col_a:
    name = st.text_input("Full Name", placeholder="e.g. James Smith")
    postcode = st.text_input("Enter Postcode", value="SW1A 1AA")
with col_b:
    dob = st.date_input("Date of Birth", format="DD/MM/YYYY", value=datetime(1990, 1, 1))
    city = st.text_input("City")

# --- 2) ADDRESS FETCHING (Pillar 1) ---
address_list = ["Enter postcode to see addresses..."]
if postcode:
    if st.button("Fetch Addresses"):
        address_list = [f"1 {postcode} Street", f"12 {postcode} Road", f"55 {postcode} Way", "Manual Entry..."]
selected_address = st.selectbox("Address Line 1", options=address_list)

# --- 3) LIVE CRIME API (Pillar 2) ---
v_crimes, acc_score = 0, 0
if postcode and len(postcode) > 4:
    try:
        geo = requests.get(f"https://api.postcodes.io/postcodes/{postcode}").json()
        if geo.get('status') == 200:
            lat, lng = geo['result']['latitude'], geo['result']['longitude']
            crimes = requests.get(f"https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}").json()
            v_crimes = len([c for c in crimes if "vehicle" in c['category'].lower()])
            acc_score = len(crimes) // 20 
    except: pass

# --- 4) 21-DAY TEST DRIVE (Pillar 3) ---
st.divider()
st.subheader("🏁 Phase 1: 21-Day Test Drive")
if "test_drive_active" not in st.session_state: 
    st.session_state.test_drive_active = False

if st.button("🚀 Start 21-Day Monitoring"):
    with st.status("Building Motion DNA profile...", expanded=True) as status:
        time.sleep(1); st.write("📡 Calibrating sensors..."); time.sleep(1)
        st.write("📵 Monitoring distraction events..."); time.sleep(1)
        status.update(label="21 Days Complete!", state="complete", expanded=False)
    st.session_state.test_drive_active = True

# --- 5) UNDERWRITING, DISTRACTION & DECLINE (Pillars 4 & 5) ---
if st.session_state.test_drive_active:
    st.subheader("Your Test Drive Results")
    col1, col2, col3 = st.columns(3)
    braking = col1.slider("Harsh Braking", 0, 20, 2, disabled=True)
    speeding = col2.slider("Speeding Events", 0, 10, 0, disabled=True)
    distraction = col3.slider("Phone Usage", 0, 10, 1, disabled=True)
    
    accidents = st.number_input("Prior Accidents (Last 5 Years)", value=int(acc_score))
    crime_rate_val = st.number_input("Local Vehicle Crime Rate", value=int(v_crimes))
    
    if st.button("Review My Eligibility"):
        total_risk = braking + (speeding * 2) + (distraction * 3)
        
        if total_risk > 12:
            st.error("❌ Sorry, we cannot offer you a policy based on your Test Drive behavior.")
        else:
            discount = max(0, 45 - (total_risk * 3))
            base_price = 500 + (accidents * 150) + (crime_rate_val * 10)
            final_price = base_price * (1 - (discount / 100))
            st.balloons(); st.success("✅ Eligibility Confirmed!")
            st.metric(f"Personalised Premium", f"£{final_price:,.2f}", f"-{discount}% Performance Discount")

            df = pd.DataFrame([[name, dob.strftime('%d-%b-%Y'), postcode, selected_address, accidents, crime_rate_val, final_price]], 
                               columns=['Name', 'DOB', 'Postcode', 'Address', 'Accidents', 'Crime_Rate', 'Premium'])
            df.to_csv('quotes.csv', mode='a', index=False, header=not os.path.isfile('quotes.csv'))

# --- 6) HISTORY ---
if os.path.isfile('quotes.csv') and os.path.getsize('quotes.csv') > 0:
    st.markdown("---")
    st.subheader("📜 Recent Accepted Quotes")
    try: st.dataframe(pd.read_csv('quotes.csv').tail(3), use_container_width=True)
    except: os.remove('quotes.csv')
