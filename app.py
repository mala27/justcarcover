# Project Link: https://urban-spoon-ww564pwxqrcgggv.github.dev/
# Master Version: v0.15 Prior to v0.01-Saga (See Github's Version Control Files for Details)


import streamlit as st #Engine powering user interface & enter boxes
import pandas as pd #Housekeeping tool for organizing/saving quotes in CSV
import os #Manage system paths
import time #Timestamps for every new quote generated
import datetime
import hmac, hashlib
import json #For saving Smartcar credentials securely
import requests #Talking to external APIs
import smartcar #Heavy lifting & talking to external APIs & vehicles itself
import io
import uuid
from cryptography.fernet import Fernet


# Our hidden storage for users details saved & associated it with the claim tickets
@st.cache_resource
def get_server_vault():
    return {}

vault = get_server_vault()


# 1. THE RESTORATION VAULT: Unpack the "claim ticket" before any widgets render (checked Monday, 9-Mar)
if "state" in st.query_params and not st.session_state.get("_restored"):
    ticket = st.query_params["state"]
    if ticket in vault:
        # v.01 Saga Restoration: Mapping new users-data fields back specifically
        user_data = vault.get(ticket)
        st.session_state.f_name = user_data.get("f_name", "")
        st.session_state.s_name = user_data.get("s_name", "")
        st.session_state.gender = user_data.get("gender", "Male")
        st.session_state.postcode = user_data.get("postcode", "")
        st.session_state.selected_address = user_data.get("selected_address", "")
        st.session_state.dob_text = user_data.get("dob_text", "")
        st.session_state.homeowner = user_data.get("homeowner", True)
        st.session_state.car_reg = user_data.get("car_reg", "")
        st.session_state.test_drive_active = user_data.get("test_drive_active", False)
        st.session_state.lat = user_data.get("lat", 51.5074)
        st.session_state.lng = user_data.get("lng", -0.1278)

        st.session_state["_restored"] = True
        st.query_params.clear()
        st.rerun()

    
# SAFE DEFAULTS: This ensures Streamlit doesn't wipe the above values when widgets load
st.session_state.setdefault("f_name", "")
st.session_state.setdefault("s_name", "")
st.session_state.setdefault("gender", "Male")
st.session_state.setdefault("postcode", "")
st.session_state.setdefault("selected_address", "")
st.session_state.setdefault("dob_text", "")
st.session_state.setdefault("homeowner", True)
st.session_state.setdefault("car_reg", "")
st.session_state.setdefault("test_drive_active", False)
st.session_state.setdefault("lat", 51.5074)
st.session_state.setdefault("lng", -0.1278)
st.session_state.setdefault("mileage", 0.0)


# Smartcar Webhook Handshake & Error Listener (checked Monday, 9-Mar)
def handle_webhook():
    if st.query_params.get("webhook") == "true":
        payload_bytes = st.context.headers.get("x-body-raw", b"") 
        if not payload_bytes: st.stop()
        signature = st.context.headers.get("sc-signature")
        secret = st.secrets["SMARTCAR_WEBHOOK_SECRET"]
        expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected): st.stop()
        data = json.loads(payload_bytes)
        if data.get("eventType") == "VERIFY":
            challenge = data["data"]["challenge"]
            answer = hmac.new(secret.encode(), challenge.encode(), hashlib.sha256).hexdigest()
            st.json({"challenge": answer}) 
            st.stop()     
        if data.get("eventType") == "VEHICLE_ERROR":
            error_code = data.get("data", {}).get("code")
            owner_actions = {"IGNITION_ON": "🔑 Engine off to sync.", "IN_MOTION": "🚗 Car moving!", "ASLEEP": "💤 Car asleep."}
            st.warning(owner_actions.get(error_code, f"Vehicle Issue: {error_code}"))
            st.stop()

handle_webhook()


# --- 1) SAAS GUI BRANDING & THEME ---
st.set_page_config(page_title="justcarcover | Saga Portal", layout="wide")

# --- NAVIGATION BAR ---
nav_col1, nav_col2 = st.columns([3, 1])
with nav_col1:
    st.markdown("""
        <div style="display: flex; gap: 30px; align-items: center; font-family: sans-serif; font-weight: 500; margin-bottom: 10px;">
            <span style="cursor: pointer; color: #111;">Home</span>
            <span style="cursor: pointer; color: #666;">FAQ</span>
            <span style="cursor: pointer; color: #666;">About Us</span>
        </div>
    """, unsafe_allow_html=True)
with nav_col2:
    st.markdown("""
        <div style="text-align: right; font-family: sans-serif; font-weight: 600; color: #013a63; cursor: pointer;">
            MyAccount
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Lemonade-inspired Soft UI */
    .stApp { background-color: #ffffff; } 
    
    /* Saga Green Toggle Fix - Now Safely Inside CSS Block */
    div[data-testid="stCheckbox"] div[role="switch"][aria-checked="true"] {
        background-color: #2e7d32 !important;
    }
      
    div[data-testid="stMetric"] {
        background-color: #f9f9fb;
        border: none !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    
    div.stButton > button { 
        background-color: #013a63 !important; 
        color: white !important; 
        border-radius: 30px !important; 
        border: none !important;
        padding: 0px 40px !important;
        transition: all 0.3s ease;
    }

    .stTextInput input, .stDateInput input, .stSelectbox [data-baseweb="select"] {
        border-radius: 12px !important;
        border: 1px solid #eee !important;
        background-color: #fafafa !important;
    }
    </style>
    """, unsafe_allow_html=True)



# --- BRANDING LOGO & TITLE ---
col_logo, col_text = st.columns([1.5, 5])
with col_logo:
    st.image("https://raw.githubusercontent.com/mala27/justcarcover/main/logo.png", width=200)
with col_text:
    st.title("justcarcover | Specialist Broker Portal")
    st.caption("v0.15 Smart-Price Engine | Soft UI Active")
st.divider()


#Clever way to prevent a blank dropdown, from looking like a bug (checked Monday, 9-Mar)
if "address_options" not in st.session_state:
    st.session_state.address_options = ["Enter postcode to see addresses..."]

# --- 2) IDENTITY & POSTCODE --- (checked Monday, 9-Mar)
#Splitting into col_a & col_b makes portal looking professional application
if "selected_address" not in st.session_state: st.session_state.selected_address = "Enter postcode to see addresses..."

col_a, col_b = st.columns(2)
with col_a:
    f_name = st.text_input("First Name", key="f_name")
    s_name = st.text_input("Surname", key="s_name")
    postcode = st.text_input("Enter Postcode", key="postcode")

with col_b:
    # 1. Saga-Style Text Entry
    dob_text = st.text_input("Date of Birth", value=st.session_state.get("dob_text", ""), placeholder="DD/MM/YYYY", key="dob_text")
    
    # 2. Validation Logic
    dob_val = None
    if dob_text:
        try:
            dob_val = datetime.datetime.strptime(dob_text, "%d/%m/%Y").date()
            st.caption("✅ Date Verified")
        except ValueError:
            st.error("⚠️ Use DD/MM/YYYY format")

    is_homeowner = st.toggle("Are you a homeowner?", value=True, key="homeowner") 
    reg_no = st.text_input("Car Reg No", key="car_reg", placeholder="e.g. AB12 CDE")
    


#Surgical Update: it automates boring stuff of calling addresses (checked Monday, 9-Mar)
#Surgical Update: from Ideal Postcodes for professional-grade accuracy
#Clean logic to display the selected address without errors
current_sel = st.session_state.get('selected_address', "")
display_val = current_sel if "Enter postcode" not in current_sel else ""
address_field = st.text_input("Address", value=display_val)


# 3) ADDRESS FETCHING (Pillar 1) - (checked Monday, 9-Mar)
# v0.12 - Syncing API fetch with verified session state
if st.button("🔍 Fetch Verified Addresses"):
    # Pull directly from session_state to ensure it's the latest typed value
    search_postcode = st.session_state.get("postcode", "").replace(" ", "").upper()
    
    if search_postcode:
        API_KEY = st.secrets["IDEAL_POSTCODES_KEY"]
        url = f"https://api.ideal-postcodes.co.uk/v1/postcodes/{search_postcode}?api_key={API_KEY}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                addresses = data.get('result', [])
                if addresses:
                    st.session_state.address_options = [f"{a['line_1']}, {a['line_2']}".strip(', ') for a in addresses]
                    st.session_state.address_options.append("Manual Entry...")
                    st.session_state.lat = addresses[0].get('latitude', 51.5074)
                    st.session_state.lng = addresses[0].get('longitude', -0.1278)
                    st.rerun() # Refresh to show new options in selectbox
                else:
                    st.warning(f"No addresses found for {search_postcode}. Try another.")
            else:
                st.error(f"API Issue: {response.json().get('message', 'Unknown Error')}")
        except Exception as e:
            st.error(f"Connection error: {e}")



# This line must be OUTSIDE the button block so it stays visible (checked Monday, 9-Mar)
st.session_state.selected_address = st.selectbox("Address Line 1", options=st.session_state.address_options)


# --- 4) LIVE CRIME API (Pillar 2) --- (checked Monday, 9-Mar)
v_crimes, acc_score = 0, 0
# We use the coordinates already fetched from Ideal Postcodes in Pillar 1
if "lat" in st.session_state and "lng" in st.session_state:
    try:
        crimes = requests.get(f"https://data.police.uk/api/crimes-street/all-crime?lat={st.session_state.lat}&lng={st.session_state.lng}").json()
        v_crimes = len([c for c in crimes if "vehicle" in c['category'].lower()])
        acc_score = len(crimes) // 20 
    except: pass


# --- 5) REAL SMARTCAR CONNECTION (Pillar 3) --- (checked Monday, 9-Mar)


# Tidy Priority 1: Replace hardcoded strings with st.secrets (checked Monday, 9-Mar)
# Housekeeping: Implements Atomic Token Rotation to prevent race conditions during refresh
client = smartcar.AuthClient(
    client_id=st.secrets["SMARTCAR_CLIENT_ID"],
    client_secret=st.secrets["SMARTCAR_CLIENT_SECRET"],
    redirect_uri=st.secrets["SMARTCAR_REDIRECT_URI"],
    test_mode=True
) 

# v0.11 - Minimized OAuth Scopes (Requesting only necessary data) (checked Monday, 9-Mar)
scope = ['read_vehicle_info', 'read_vin', 'read_odometer']

def get_valid_access_token():
    """Housekeeping: Fixes the attribute error by using manual timestamp check."""
    try:
        with open('urban_spoon_creds.json', 'r') as f:
            creds = json.load(f)
        
        # Check if current time is past the expiration timestamp (checked Monday, 9-Mar)
        # creds['expiration'] is saved as a string, so we convert to compare
        is_expired = datetime.datetime.now() > datetime.datetime.fromisoformat(creds['expiration'].split('+')[0])

        if is_expired:
            # v0.12 - Securely rotating tokens and updating local cache
            new_creds = client.exchange_refresh_token(creds['refresh_token'])
            
            # Housekeeping: Handle both NamedTuple and Dictionary returns
            updated_creds = new_creds._asdict() if hasattr(new_creds, '_asdict') else new_creds
            
            with open('urban_spoon_creds.json', 'w') as f:
                json.dump(updated_creds, f, default=str)
            return updated_creds['access_token']


        return creds['access_token']
    except Exception as e:
        # Fallback for first-time setup or missing file
        return None


# 1. ADD THIS LINE (The "Passport Check"): (checked Monday, 9-Mar)
code = st.query_params.get("code")


# Handling the Callback (Surgical Update: Persistence Fix for v.01 Saga)
if st.button("🔌 Connect Your Real Car"):
    state = str(uuid.uuid4())
    # Joshua's Save: Storing the full users-data into the Vault before Smartcar exit
    vault[state] = {
        "f_name": st.session_state.get("f_name", ""),
        "s_name": st.session_state.get("s_name", ""),
        "gender": st.session_state.get("gender", "Male"),
        "postcode": st.session_state.get("postcode", ""),
        "selected_address": st.session_state.get("selected_address", ""),
        "dob_text": st.session_state.get("dob_text", ""),
        "homeowner": st.session_state.get("homeowner", True),
        "car_reg": st.session_state.get("car_reg", ""),
        "lat": st.session_state.get("lat", 51.5074),
        "lng": st.session_state.get("lng", -0.1278),
        "test_drive_active": True
    }
    auth_url = client.get_auth_url(scope, options={"state": state, "force_prompt": True})
    st.link_button("Confirm Connection Details", auth_url)


# 3. Handling the Callback (v0.12 Phase 4: Error Mapping & Token Logic) (checked Monday, 9-Mar)
error_type = st.query_params.get("error")
if error_type:
    error_map = {
        "no_vehicles": "🚗 No cars found! Add your vehicle to your manufacturer's app first.",
        "vehicle_incompatible": "❌ This car lacks the hardware for smart data features.",
        "invalid_subscription": "🔑 Connected services expired. Please re-activate your data plan.",
        "access_denied": "🚫 Permission required to calculate your discount!"
    }
    st.error(error_map.get(error_type, f"Error: {error_type}"))
    st.stop()

valid_token = None
if code and not st.session_state.get('test_drive_active'):
    valid_token = get_valid_access_token()


if valid_token and not st.session_state.get('test_drive_active'):
    try:
        vehicles_response = smartcar.get_vehicles(valid_token)
        vehicle_ids = vehicles_response.vehicles
        vehicle = smartcar.Vehicle(vehicle_ids[0], valid_token)

        try:
            odometer = vehicle.odometer()
            st.session_state.mileage = odometer.distance
            st.session_state.test_drive_active = True 
            st.query_params.clear()
            st.rerun() 
        except smartcar.SmartcarException as e:
            st.error(f"Car Error: {e.suggested_user_message or 'Check connection'}")
    except Exception as e:
        st.error(f"Real-time fetch failed: {e}")


# --- 6) UPDATED UNDERWRITING (Surgical Update: Odometer Lock-in) --- (checked Monday, 9-Mar)
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
            total_discount = perf_discount + mileage_bonus 
            base_price = 500 + (accidents * 150) + (crime_rate_val * 10)
            final_price = base_price * (1 - (total_discount / 100))

            st.balloons()
            st.success(f"✅ ELIGIBILITY CONFIRMED FOR {reg_no}")
            st.metric(f"Personalised Premium", f"£{final_price:,.2f}", f"-{total_discount}% Verified Discount")


# 1. Create the df FIRST (checked Monday, 13-Mar)
            safe_dob = dob if dob else datetime.date(1975, 1, 1)
            df = pd.DataFrame([[f"{f_name} {s_name}", safe_dob.strftime('%d-%b-%Y'), postcode, address_field, accidents, crime_rate_val, st.session_state.mileage, final_price]], 
                               columns=['Name', 'DOB', 'Postcode', 'Address', 'Accidents', 'Crime_Rate', 'Verified_Miles', 'Premium'])

            # 2. THEN store it and show the button
            st.session_state.df = df 
            st.download_button("📥 Download Your Quote", st.session_state.df.to_csv(index=False), "My_Urban_Spoon_Quote.csv", "text/csv")
           
            
            # 3. Update CSV log (v0.13 Encrypted Write)
            f = Fernet(st.secrets["ENCRYPTION_KEY"].encode())
            with open('quotes.csv', 'ab') as file:
                file.write(f.encrypt(df.to_csv(index=False).encode()) + b"\n")



# --- 7) HISTORY ---(checked Monday, 9-Mar)
if os.path.isfile('quotes.csv') and os.path.getsize('quotes.csv') > 0:
    st.markdown("---")
    st.subheader("📜 Recent Submissions")
    try:
        f = Fernet(st.secrets["ENCRYPTION_KEY"].encode())
        with open('quotes.csv', 'rb') as file:
            decrypted_rows = [f.decrypt(line.strip()).decode() for line in file if line.strip()]
        
        if decrypted_rows:
            history_df = pd.concat([pd.read_csv(io.StringIO(res)) for res in decrypted_rows], ignore_index=True)
            st.dataframe(history_df.tail(3), use_container_width=True)
    except: 
        st.warning("Encryption key mismatch or corrupted log.")
        