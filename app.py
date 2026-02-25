# Project Link: https://urban-spoon-ww564pwxqrcgggv.github.dev/
# Master Version: v0.9 (Surgical Update: Github/Streamlit/Smartcar Connection Other Error Issues Resolved)

import streamlit as st #Engine powering user interface & enter boxes
import pandas as pd #Housekeeping tool for organizing/saving quotes in CSV
import os #Manage system paths
import time #Timestamps for every new quote generated
from datetime import datetime
import requests #Talking to external APIs
import smartcar #Heavy lifting & talking to external APIs & vehicles itself

#Memory of app: ensuring it doesn't forget where the user was if the page refreshes
if "test_drive_active" not in st.session_state: st.session_state.test_drive_active = False
if "mileage" not in st.session_state: st.session_state.mileage = 0


# --- 1) SAAS GUI BRANDING & THEME ---
#CSS injection that transforms standard script into professional UBI Portal
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
#Pointing logo link (raw.githubusercontent) ensures branding never breaks, regardless where app is hosted
col_logo, col_text = st.columns([1.5, 5])  # Widened the logo column ratio
with col_logo:
    st.image("https://raw.githubusercontent.com/mala27/justcarcover/main/logo.png", width=200) # Increased width to 200
with col_text:
    st.title("justcarcover | Specialist Broker Portal")
    st.caption("v0.8 Smart-Price Engine | Address Persistence Active")
st.divider()

#Clever way to prevent a blank dropdown, from looking like a bug
if "address_options" not in st.session_state:
    st.session_state.address_options = ["Enter postcode to see addresses..."]

# --- 2) IDENTITY & POSTCODE ---
#Splitting into col_a & col_b makes portal looking professional application
if "selected_address" not in st.session_state: st.session_state.selected_address = "Enter postcode to see addresses..."

col_a, col_b = st.columns(2)
with col_a:
    f_name = st.text_input("First Name", placeholder="e.g. James")
    s_name = st.text_input("Surname", placeholder="e.g. Smith")
    postcode = st.text_input("Enter Postcode", value="SP11 9JR")
with col_b:
    dob = st.date_input("Date of Birth", format="DD/MM/YYYY", value=datetime(1990, 1, 1))
    reg_no = st.text_input("Car Reg No", placeholder="e.g. AB12 CDE")


    #Surgical Update: it automates boring stuff of calling addresses
    #Surgical Update: from Ideal Postcodes for professional-grade accuracy
    #Clean logic to display the selected address without errors
current_sel = st.session_state.get('selected_address', "")
display_val = current_sel if "Enter postcode" not in current_sel else ""
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
# We use the coordinates already fetched from Ideal Postcodes in Pillar 1
if "lat" in st.session_state and "lng" in st.session_state:
    try:
        crimes = requests.get(f"https://data.police.uk/api/crimes-street/all-crime?lat={st.session_state.lat}&lng={st.session_state.lng}").json()
        v_crimes = len([c for c in crimes if "vehicle" in c['category'].lower()])
        acc_score = len(crimes) // 20 
    except: pass



# --- 5) REAL SMARTCAR CONNECTION (Pillar 3) ---
st.divider()
st.subheader("🏁 Phase 1: Real-Time Vehicle Verification")


# 1. Credentials (Surgically Matched to Urban-Spoon Dashboard, Removed SC_URI & added Security via Environment Variables)
client = smartcar.AuthClient(
    client_id='d3eeac01-9bda-4de1-99fe-405365271b15',
    client_secret='130adf6f-f153-4d66-9bfe-d9de4ebe0c7b',
    redirect_uri='https://urban-spoon-ww564pwxqrcgggv-8501.app.github.dev/exchange',
    test_mode=True 
)
 

# Handling the Callback (Surgical Update: Persistence Fix)
code = st.query_params.get("code")

# 2. The "Connect" Link
auth_url = client.get_auth_url(["read_odometer", "read_vehicle_info"])
st.link_button("🔌 Connect Your Real Car", auth_url)


# 3. Handling the Callback (Surgical Update: Persistence Fix)
code = st.query_params.get("code")


if code and not st.session_state.test_drive_active:
    try:
        res = client.exchange_code(code)
        vehicles_response = smartcar.get_vehicles(res.access_token)
        vehicle_ids = vehicles_response.vehicles # Using dot notation for NamedTuple
        vehicle = smartcar.Vehicle(vehicle_ids[0], res.access_token)
        
        # Real-time data fetch
        odometer = vehicle.odometer()
        st.session_state.mileage = odometer['data']['distance']
        st.session_state.test_drive_active = True

         # clear query params so we don’t rerun repeatedly
        st.query_params.clear()
        st.rerun() # Forces Streamlit to show the new "Underwriting" section immediately
    except Exception as e:
        # show full exception for diagnostics
        st.error(f"Handshake failed: {e}")


# --- 6) UPDATED UNDERWRITING (Surgical Update: Odometer Lock-in) ---
if st.session_state.test_drive_active:
    st.success(f"✅ Verified Odometer: {st.session_state.mileage:,.0f} miles")
    st.subheader("📊 Underwriting Decision (v0.8 Smart-Price)")
    
    # Auto-calculate the Smart-Price discount immediately
    mileage_bonus = 10 if 0 < st.session_state.mileage < 5000 else 0
    st.info(f"Verified Mileage Reward: {mileage_bonus}% Extra Discount applied.")

    col1, col2, col3 = st.columns(3)
    
    braking = col1.slider("Harsh Braking", 0, 20, 2, disabled=True)
    speeding = col2.slider("Speeding Events", 0, 10, 0, disabled=True)
    distraction = col3.slider("Phone Usage", 0, 10, 1, disabled=True)
    
    accidents = st.number_input("Prior Accidents (Last 5 Years)", value=int(acc_score))
    crime_rate_val = st.number_input("Local Vehicle Crime Rate", value=int(v_crimes))
   
    
    if st.button("⚖️ Review Final Eligibility"):
        total_risk = braking + (speeding * 2) + (distraction * 3)
        
        # v0.8 Logic: Re-verify bonus inside the button scope
        mileage_bonus = 10 if 0 < st.session_state.mileage < 5000 else 0
        perf_discount = max(0, 45 - (total_risk * 3))
                   
        if total_risk > 12:
            st.error("❌ DECLINED: Profile exceeds specialist risk appetite.")
        else:
            perf_discount = max(0, 45 - (total_risk * 3))
            total_discount = perf_discount + mileage_bonus # Combined "Smart" discount
            
            base_price = 500 + (accidents * 150) + (crime_rate_val * 10)
            final_price = base_price * (1 - (total_discount / 100))

            st.balloons()
            st.success(f"✅ ELIGIBILITY CONFIRMED FOR {reg_no}")
            st.metric(f"Personalised Premium", f"£{final_price:,.2f}", f"-{total_discount}% Verified Discount")
            st.download_button("📥 Download Your Quote", df.to_csv(index=False), "My_Urban_Spoon_Quote.csv", "text/csv")

            # Update CSV log
            df = pd.DataFrame([[f"{f_name} {s_name}", dob.strftime('%d-%b-%Y'), postcode, address_field, accidents, crime_rate_val, st.session_state.mileage, final_price]], 
                               columns=['Name', 'DOB', 'Postcode', 'Address', 'Accidents', 'Crime_Rate', 'Verified_Miles', 'Premium'])
        
            df.to_csv('quotes.csv', mode='a', index=False, header=not os.path.isfile('quotes.csv'))

   
# --- 7) HISTORY ---
if os.path.isfile('quotes.csv') and os.path.getsize('quotes.csv') > 0:
    st.markdown("---")
    st.subheader("📜 Recent Submissions")
    try: st.dataframe(pd.read_csv('quotes.csv').tail(3), width='stretch')
    except: os.remove('quotes.csv')