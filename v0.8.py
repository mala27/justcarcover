# Project Link: https://automatic-trout-6j56pqjx9vfxrr7-8501.app.github.dev/
# Version: v0.6.4 - MASTER (Surgical Update: Address Persistence & City Auto-fill)

import streamlit as st
import requests
import pandas as pd
import os
import time
from datetime import datetime

# --- 1) SAAS UI BRANDING & THEME ---
st.set_page_config(page_title="justcarcover | Broker Portal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    div.stButton > button { 
        background-color: #013a63 !important; 
        color: white !important; 
        border-radius: 10px !important;
        height: 3.5em !important;
        font-weight: bold !important;
        border: none !important;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING LOGO & TITLE ---
col_logo, col_text = st.columns([1.5, 5])  # Widened the logo column ratio
with col_logo:
    st.image("https://raw.githubusercontent.com/mala27/justcarcover/main/logo.png", width=200) # Increased width to 200
with col_text:
    st.title("justcarcover | Specialist Broker Portal")
    st.caption("v0.7 Master Engine | Address Persistence Active")
st.divider()

if "address_options" not in st.session_state:
    st.session_state.address_options = ["Enter postcode to see addresses..."]

# --- 2) IDENTITY & POSTCODE ---
if "address_options" not in st.session_state:
    st.session_state.address_options = ["Enter postcode to see addresses..."]
if "selected_address" not in st.session_state: st.session_state.selected_address = "Enter postcode to see addresses..."

col_a, col_b = st.columns(2)
with col_a:
    f_name = st.text_input("First Name", placeholder="e.g. James")
    s_name = st.text_input("Surname", placeholder="e.g. Smith")
    postcode = st.text_input("Enter Postcode", value="SP11 9JR")
with col_b:
    dob = st.date_input("Date of Birth", format="DD/MM/YYYY", value=datetime(1990, 1, 1))
    reg_no = st.text_input("Car Reg No", placeholder="e.g. AB12 CDE")


    # Surgical Update: Auto-fill city logic
    city_val = ""
    if postcode and len(postcode) > 4:
        try:
            geo_data = requests.get(f"https://api.postcodes.io/postcodes/{postcode}").json()
            if geo_data.get('status') == 200:
                city_val = geo_data['result'].get('admin_ward') or geo_data['result'].get('parliamentary_constituency')
        except: pass
     # Clean logic to combine the selected address and city without errors
    current_sel = st.session_state.get('selected_address', "")
    display_val = f"{current_sel}, {city_val}".strip(", ") if "Enter postcode" not in current_sel else city_val
    address_field = st.text_input("Address", value=display_val)

# --- 3) ADDRESS FETCHING (Pillar 1) ---
if st.button("🔍 Fetch Verified Addresses"):
    if postcode:
        # Replace 'your_key_here' with your actual ak_ key from the dashboard
        API_KEY = "ak_mlqkm51v9g4QpYFoD2ZHD76Ow3V8g" 
        url = f"https://api.ideal-postcodes.co.uk/v1/postcodes/{postcode.replace(' ', '')}?api_key={API_KEY}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                addresses = data.get('result', [])
                # This pulls real line-level data for your dropdown
                st.session_state.address_options = [f"{a['line_1']}, {a['line_2']}".strip(', ') for a in addresses]
                st.session_state.address_options.append("Manual Entry...")
            else:
                st.error("Address not found or API issue.")
        except:
            st.error("Connection error.")

# This line must be OUTSIDE the button block so it stays visible
st.session_state.selected_address = st.selectbox("Address Line 1", options=st.session_state.address_options)

# --- 4) LIVE CRIME API (Pillar 2) ---
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

# --- 5) 21-DAY TEST DRIVE (Pillar 3) ---
st.divider()
st.subheader("🏁 Phase 1: 21-Day Test Drive Monitoring")
if "test_drive_active" not in st.session_state: 
    st.session_state.test_drive_active = False

if st.button("🚀 Start 21-Day Monitoring"):
    with st.status("Building Motion DNA profile...", expanded=True) as status:
        time.sleep(1); st.write("📡 Calibrating sensors..."); time.sleep(1)
        st.write("📵 Monitoring distraction events..."); time.sleep(1)
        status.update(label="21 Days Complete!", state="complete", expanded=False)
    st.session_state.test_drive_active = True

# --- 6) UNDERWRITING, DISTRACTION & DECLINE (Pillars 4 & 5) ---
if st.session_state.test_drive_active:
    st.subheader("📊 Underwriting Decision")
    col1, col2, col3 = st.columns(3)
    braking = col1.slider("Harsh Braking", 0, 20, 2, disabled=True)
    speeding = col2.slider("Speeding Events", 0, 10, 0, disabled=True)
    distraction = col3.slider("Phone Usage", 0, 10, 1, disabled=True)
    
    accidents = st.number_input("Prior Accidents (Last 5 Years)", value=int(acc_score))
    crime_rate_val = st.number_input("Local Vehicle Crime Rate", value=int(v_crimes))
    
    if st.button("⚖️ Review Final Eligibility"):
        total_risk = braking + (speeding * 2) + (distraction * 3)
        
        if total_risk > 12:
            st.error("❌ DECLINED: Profile exceeds specialist risk appetite.")
        else:
            discount = max(0, 45 - (total_risk * 3))
            base_price = 500 + (accidents * 150) + (crime_rate_val * 10)
            final_price = base_price * (1 - (discount / 100))
            st.balloons(); st.success(f"✅ ELIGIBILITY CONFIRMED FOR {reg_no}")
            st.metric(f"Personalised Premium", f"£{final_price:,.2f}", f"-{discount}% Performance Discount")

            df = pd.DataFrame([[f"{f_name} {s_name}", dob.strftime('%d-%b-%Y'), postcode, address_field, accidents, crime_rate_val, final_price]], 
                               columns=['Name', 'DOB', 'Postcode', 'Address', 'Accidents', 'Crime_Rate', 'Premium'])
            df.to_csv('quotes.csv', mode='a', index=False, header=not os.path.isfile('quotes.csv'))

# --- 7) HISTORY ---
if os.path.isfile('quotes.csv') and os.path.getsize('quotes.csv') > 0:
    st.markdown("---")
    st.subheader("📜 Recent Submissions")
    try: st.dataframe(pd.read_csv('quotes.csv').tail(3), width='stretch')
    except: os.remove('quotes.csv')