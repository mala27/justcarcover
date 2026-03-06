# Project Link: https://urban-spoon-ww564pwxqrcgggv.github.dev/
# Master Version: v0.13 (See Github's Version Control Files for Details)


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
from cryptography.fernet import Fernet


# Smartcar Webhook Handshake & Error Listener (code checked 6-Mar-26)
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


# Memory of app: ensuring it doesn't forget where the user was if the page refreshes (checked code on 6-Mar-26)
if "test_drive_active" not in st.session_state: st.session_state.test_drive_active = "code" in st.query_params
if "mileage" not in st.session_state: st.session_state.mileage = int(st.query_params.get("mileage", 0))
if "first_name" not in st.session_state: st.session_state.first_name = st.query_params.get("first_name", "")
if "surname" not in st.session_state: st.session_state.surname = st.query_params.get("surname", "")
if "postcode" not in st.session_state: st.session_state.postcode = st.query_params.get("postcode", "")
if "selected_address" not in st.session_state: st.session_state.selected_address = st.query_params.get("selected_address", "")
if "dob" not in st.session_state: st.session_state.dob = st.query_params.get("dob", "")
if "car_reg" not in st.session_state: st.session_state.car_reg = st.query_params.get("car_reg", "")


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
    f_name = st.text_input("First Name", key="f_name", placeholder="e.g. James")
    s_name = st.text_input("Surname", key="s_name", placeholder="e.g. Smith")
    postcode = st.text_input("Enter Postcode", key="postcode", value="SP11 9JR")

with col_b:
    # Indented to stay inside col_b
    dob = st.date_input(
        "Enter Date of Birth",
        value=datetime.date(1975, 1, 1),
        min_value=datetime.date(1935, 1, 1), 
        max_value=datetime.date.today(),
        format="DD/MM/YYYY" # This forces the British display format
    )
    
    reg_no = st.text_input("Car Reg No", placeholder="e.g. AB12 CDE")


    #Surgical Update: it automates boring stuff of calling addresses
    #Surgical Update: from Ideal Postcodes for professional-grade accuracy
    #Clean logic to display the selected address without errors
current_sel = st.session_state.get('selected_address', "")
display_val = current_sel if "Enter postcode" not in current_sel else ""
address_field = st.text_input("Address", value=display_val)


# 3) ADDRESS FETCHING (Pillar 1)
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
                    st.rerun() # Refresh to show new options in selectbox
                else:
                    st.warning(f"No addresses found for {search_postcode}. Try another.")
            else:
                st.error(f"API Issue: {response.json().get('message', 'Unknown Error')}")
        except Exception as e:
            st.error(f"Connection error: {e}")



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

 
# Tidy Priority 1: Replace hardcoded strings with st.secrets
# Housekeeping: Implements Atomic Token Rotation to prevent race conditions during refresh
client = smartcar.AuthClient(
    client_id=st.secrets["SMARTCAR_CLIENT_ID"],
    client_secret=st.secrets["SMARTCAR_CLIENT_SECRET"],
    redirect_uri=st.secrets["SMARTCAR_REDIRECT_URI"],
    test_mode=True
) 

# v0.11 - Minimized OAuth Scopes (Requesting only necessary data)
scope = ['read_vehicle_info', 'read_vin', 'read_odometer']



def get_valid_access_token():
    """Housekeeping: Fixes the attribute error by using manual timestamp check."""
    try:
        with open('urban_spoon_creds.json', 'r') as f:
            creds = json.load(f)
        
        # Check if current time is past the expiration timestamp
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



# Handling the Callback (Surgical Update: Persistence Fix)
code = st.query_params.get("code")

# 2. The "Connect" Link & Make OEMs Acceptance Automatic
auth_url = client.get_auth_url(scope)
st.link_button("🔌 Connect Your Real Car", auth_url)


# 3. Handling the Callback (v0.12 Phase 4: Error Mapping & Token Logic)
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
            total_discount = perf_discount + mileage_bonus 
            base_price = 500 + (accidents * 150) + (crime_rate_val * 10)
            final_price = base_price * (1 - (total_discount / 100))

            st.balloons()
            st.success(f"✅ ELIGIBILITY CONFIRMED FOR {reg_no}")
            st.metric(f"Personalised Premium", f"£{final_price:,.2f}", f"-{total_discount}% Verified Discount")

# 1. Create the df FIRST
            df = pd.DataFrame([[f"{f_name} {s_name}", dob.strftime('%d-%b-%Y'), postcode, address_field, accidents, crime_rate_val, st.session_state.mileage, final_price]], 
                               columns=['Name', 'DOB', 'Postcode', 'Address', 'Accidents', 'Crime_Rate', 'Verified_Miles', 'Premium'])

            # 2. THEN store it and show the button
            st.session_state.df = df 
            st.download_button("📥 Download Your Quote", st.session_state.df.to_csv(index=False), "My_Urban_Spoon_Quote.csv", "text/csv")
           
            
            # 3. Update CSV log (v0.13 Encrypted Write)
            f = Fernet(st.secrets["ENCRYPTION_KEY"].encode())
            with open('quotes.csv', 'ab') as file:
                file.write(f.encrypt(df.to_csv(index=False).encode()) + b"\n")


# --- 7) HISTORY ---
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
    except: st.warning("Encryption key mismatch or corrupted log.")

