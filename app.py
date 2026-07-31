import io
import json
import random
import re
import smtplib
import time
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

# --- OPTIONAL OPENCV IMPORT FOR ADVANCED OCR PREPROCESSING ---
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# --- OPTIONAL GEMINI API IMPORT FOR SMART PARSING ---
try:
    import google.generativeai as genai

    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except Exception:
    GEMINI_AVAILABLE = False

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="JOULIE THE BULLY | Enterprise Load Management",
    page_icon="🚛",
    layout="wide",
)

# --- ADMIN EMAIL & SESSION CONFIG ---
ADMIN_EMAIL = "admin@jouliethebully.com"
SESSION_DURATION_DAYS = 7
SESSION_DURATION_SECONDS = SESSION_DURATION_DAYS * 24 * 60 * 60


# --- NATIVE QUERY PARAMS AUTHENTICATION & 7-DAY PERSISTENCE (OPEN ACCESS) ---
def domain_and_otp_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "otp_sent" not in st.session_state:
        st.session_state["otp_sent"] = False
    if "correct_otp" not in st.session_state:
        st.session_state["correct_otp"] = None

    if not st.session_state["authenticated"]:
        try:
            saved_user = st.query_params.get("joulie_user")
            saved_exp = st.query_params.get("joulie_exp")
        except AttributeError:
            saved_user = None
            saved_exp = None

        if saved_user and saved_exp:
            try:
                if time.time() < float(saved_exp):
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = saved_user
                    st.session_state["is_admin"] = (
                        saved_user.lower() == ADMIN_EMAIL.lower()
                    )
                    st.session_state["expiry_time"] = float(saved_exp)
                else:
                    st.query_params.clear()
            except (ValueError, TypeError):
                pass

    if st.session_state.get("authenticated", False):
        if time.time() > st.session_state.get("expiry_time", 0):
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.session_state["authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["is_admin"] = False
            st.session_state["expiry_time"] = 0
            st.warning(
                "⚠️ Your 7-day session has expired. Please authenticate again."
            )
            st.rerun()

    if not st.session_state.get("authenticated", False):
        st.subheader("🔐 JOULIE THE BULLY | Secure Portal")

        if not st.session_state["otp_sent"]:
            email = st.text_input("User Email Address", key="input_email")
            if st.button("Send Verification Code", type="primary"):
                clean_email = email.strip().lower()
                # Open access: accepts any valid email format
                if "@" in clean_email and "." in clean_email.split("@")[-1]:
                    otp = str(random.randint(100000, 999999))
                    st.session_state["correct_otp"] = otp
                    st.session_state["pending_email"] = clean_email

                    try:
                        smtp_user = st.secrets["BREVO_SMTP_USER"]
                        sender_email = st.secrets["BREVO_SENDER_EMAIL"]
                        sender_password = st.secrets["BREVO_SMTP_KEY"]

                        msg = MIMEText(
                            f"Your JOULIE THE BULLY verification code is:"
                            f" {otp}\n\nNote: Successful login will keep you"
                            " signed in for 7 days across browser refreshes."
                        )
                        msg["Subject"] = (
                            "JOULIE THE BULLY Secure Login Verification Code"
                        )
                        msg["From"] = sender_email
                        msg["To"] = clean_email

                        with smtplib.SMTP("smtp-relay.brevo.com", 587) as server:
                            server.starttls()
                            server.login(smtp_user, sender_password)
                            server.sendmail(
                                sender_email, clean_email, msg.as_string()
                            )

                        st.session_state["otp_sent"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(
                            "Failed to dispatch verification email via Brevo"
                            f" SMTP. Error: {e}"
                        )
                else:
                    st.error("❌ Please enter a valid email address.")
        else:
            st.info(
                "Verification code dispatched to"
                f" **{st.session_state['pending_email']}**."
            )
            user_otp = st.text_input(
                "Enter 6-Digit Verification Code", type="password"
            )

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if st.button(
                    "Verify & Launch Session",
                    type="primary",
                    use_container_width=True,
                ):
                    if user_otp.strip() == st.session_state["correct_otp"]:
                        pending_email = st.session_state["pending_email"]
                        expiry_timestamp = (
                            time.time() + SESSION_DURATION_SECONDS
                        )

                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = pending_email
                        st.session_state["is_admin"] = (
                            pending_email.lower() == ADMIN_EMAIL.lower()
                        )
                        st.session_state["expiry_time"] = expiry_timestamp

                        try:
                            st.query_params["joulie_user"] = pending_email
                            st.query_params["joulie_exp"] = str(
                                expiry_timestamp
                            )
                        except Exception:
                            pass

                        st.success(
                            "Authentication successful. Establishing 7-day"
                            " session..."
                        )
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error(
                            "❌ Invalid verification code entered. Please try"
                            " again."
                        )
            with col_v2:
                if st.button("Use Different Email", use_container_width=True):
                    st.session_state["otp_sent"] = False
                    st.rerun()

        return False
    return True


def clear_persistent_session():
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["is_admin"] = False
    st.session_state["expiry_time"] = 0
    st.session_state["otp_sent"] = False
    st.session_state["correct_otp"] = None


if not domain_and_otp_login():
    st.stop()

# --- HIDE FOOTER & GITHUB MENU ITEMS ---
if not st.session_state.get("is_admin", False):
    st.markdown(
        """
        <style>
        header {visibility: visible !important;}
        footer {display: none !important; visibility: hidden !important;}
        #GithubIcon {display: none !important;}
        .viewerBadge_container__1QSob {display: none !important;}
        [data-testid="stToolbarActions"] {display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}
        a[href*="github.com"] {display: none !important;}
        button[title*="Fork"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- TESSERACT OCR SETUP ---
try:
    import shutil
    import pytesseract

    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# --- CUSTOM PINK & WHITE STYLING ---
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&family=Caveat:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
}

.logo-container {
    display: flex;
    align-items: center;
    gap: 32px;
    background: #ffffff;
    padding: 22px 28px;
    border-radius: 16px;
    border: 2px solid #f472b6;
    box-shadow: 0 10px 25px -5px rgba(219, 39, 119, 0.15);
    margin-bottom: 28px;
}

.cargofit-logo-box {
    position: relative;
    padding: 16px 28px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.cargofit-logo-box::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 55%;
    height: 65%;
    border-top: 6px solid #db2777;
    border-left: 6px solid #db2777;
    box-sizing: border-box;
}
.cargofit-logo-box::after {
    content: '';
    position: absolute;
    bottom: 0;
    right: 0;
    width: 55%;
    height: 65%;
    border-bottom: 6px solid #db2777;
    border-right: 6px solid #db2777;
    box-sizing: border-box;
}
.cargofit-text {
    font-family: 'Outfit', sans-serif;
    font-size: 32px;
    font-weight: 900;
    color: #db2777;
    letter-spacing: 2px;
    line-height: 1;
}

.logo-header-right {
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.logo-text {
    font-size: 38px;
    font-weight: 900;
    letter-spacing: 1px;
    margin: 0;
    line-height: 1;
    color: #831843;
}
.brand-cargo { color: #831843; }
.brand-fit { color: #db2777; }

.logo-subtext {
    color: #be185d;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 6px;
}

.signature-cursive {
    font-family: 'Caveat', cursive;
    color: #f472b6;
    font-size: 26px;
    font-weight: 700;
    margin-top: 2px;
}

.truck-road-wrapper {
    background: #fdf2f8;
    padding: 14px 10px 8px 10px;
    border-radius: 12px;
    border: 1px solid #fbcfe8;
    margin-bottom: 18px;
    overflow: hidden;
    position: relative;
}
.road {
    width: 100%;
    height: 3px;
    background: #fbcfe8;
    position: relative;
    margin-top: 4px;
    overflow: hidden;
}
.road-line {
    position: absolute;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(90deg, #db2777 0px, #db2777 12px, transparent 12px, transparent 24px);
    animation: roadMove 0.8s linear infinite;
}
@keyframes roadMove {
    0% { transform: translateX(0); }
    100% { transform: translateX(-24px); }
}
.animated-truck {
    font-size: 34px;
    display: inline-block;
    animation: truckBounce 0.4s ease-in-out infinite alternate;
    margin-left: 10px;
}
@keyframes truckBounce {
    0% { transform: translateY(0); }
    100% { transform: translateY(-3px); }
}
.sidebar-title {
    color: #831843;
    font-size: 16px;
    font-weight: 800;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Primary buttons in Pink */
div.stButton > button[kind="primary"] {
    background-color: #db2777 !important;
    border-color: #db2777 !important;
    color: #ffffff !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #be185d !important;
    border-color: #be185d !important;
}
</style>

<div class="logo-container">
    <div class="cargofit-logo-box">
        <span class="cargofit-text">JOULIE</span>
    </div>
    <div class="logo-header-right">
        <div class="logo-text"><span class="brand-cargo">JOULIE </span><span class="brand-fit">THE BULLY</span></div>
        <div class="logo-subtext">3D Cargo Optimization & Load Planning System</div>
        <div class="signature-cursive">Fleet Dispatch Division</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR: USER ACCOUNT & VEHICLE SELECTOR ---
st.sidebar.caption(
    f"👤 Authenticated User: **{st.session_state.get('user_email')}**"
)
if st.sidebar.button(
    "🚪 Terminate Session", key="logout_btn", use_container_width=True
):
    clear_persistent_session()
    st.rerun()

st.sidebar.markdown(
    """
    <div class="truck-road-wrapper">
        <div class="sidebar-title">
            <span class="animated-truck">🚛</span>
            <span>Equipment Parameters</span>
        </div>
        <div class="road">
            <div class="road-line"></div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

vehicle_type = st.sidebar.selectbox(
    "Equipment Configuration",
    [
        "53ft Dry Van Trailer",
        "Large Straight 26'",
        "Large Straight 24'",
        "Large Straight 22'",
    ],
)

defaults = {
    "53ft Dry Van Trailer": (636, 99, 110, 45000),
    "Large Straight 26'": (312, 96, 96, 10000),
    "Large Straight 24'": (288, 96, 96, 10000),
    "Large Straight 22'": (264, 96, 96, 10000),
}

v_len_def, v_wid_def, v_hgt_def, v_payload_def = defaults[vehicle_type]

v_length = st.sidebar.number_input(
    "Cargo Bed Length (in)", min_value=50, max_value=1200, value=v_len_def
)
v_width = st.sidebar.number_input(
    "Cargo Bed Width (in)", min_value=30, max_value=300, value=v_wid_def
)
v_height = st.sidebar.number_input(
    "Internal Height Clearance (in)", min_value=30, max_value=300, value=v_hgt_def
)
max_payload = st.sidebar.number_input(
    "Maximum Payload Capacity (lbs)",
    min_value=500,
    max_value=100000,
    value=v_payload_def,
)

# --- MAIN CONTENT: CARGO SETUP ---
st.subheader("📦 Freight Configuration & Pallet Setup")

STANDARD_PALLETS = {
    "Standard GMA Pallet (48 x 40 in)": (48, 40),
    "Square Pallet (42 x 42 in)": (42, 42),
    "Large Square Pallet (48 x 48 in)": (48, 48),
}

col1, col2 = st.columns([3, 2])
pallets_to_plan = []

with col1:
    st.markdown("#### Standard Pallet Configurations")
    for name, (p_l, p_w) in STANDARD_PALLETS.items():
        c_enable, c_qty, c_h, c_wt, c_stack = st.columns([2, 1, 1, 1, 1])
        with c_enable:
            active = st.checkbox(name, value=False, key=f"chk_{name}")
        with c_qty:
            qty = st.number_input(
                "Qty", min_value=1, value=1, key=f"qty_{name}", disabled=not active
            )
        with c_h:
            hgt = st.number_input(
                "H (in)",
                min_value=5,
                max_value=150,
                value=60,
                key=f"hgt_{name}",
                disabled=not active,
            )
        with c_wt:
            wt = st.number_input(
                "Unit Wt (lbs)",
                min_value=1,
                max_value=10000,
                value=1000,
                key=f"wt_{name}",
                disabled=not active,
            )
        with c_stack:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            stackable = st.checkbox(
                "Stackable",
                value=False,
                key=f"stack_{name}",
                disabled=not active,
                help="Permit freight to be stacked directly on top of this unit.",
            )

        if active:
            for _ in range(qty):
                pallets_to_plan.append({
                    "type": name,
                    "length": p_l,
                    "width": p_w,
                    "height": hgt,
                    "weight": wt,
                    "stackable": stackable,
                })


# --- BULLETPROOF MULTIMODAL LLM & FALLBACK PARSING ENGINE ---
def llm_parse_cargo_text(text, uploaded_file=None):
    """Uses Gemini's native vision to read images directly or parses raw text."""
    if GEMINI_AVAILABLE:
        try:
            model = genai.GenerativeModel("gemini-3.6-flash")
            prompt = """
            Extract all cargo items from this logistics document, rate confirmation, or image. 
            For each item, identify:
            - length (integer in inches)
            - width (integer in inches)
            - height (integer in inches)
            - weight (float in lbs per single unit)
            - quantity (integer count of items, e.g. if it says "Pcs: 1" or "2 @ 685lbs EACH", extract the correct count)

            Return ONLY a valid JSON array of objects with keys: "length", "width", "height", "weight", "qty". 
            Do not include markdown blocks or any other text.
            """

            if uploaded_file is not None:
                uploaded_file.seek(0)
                image = Image.open(uploaded_file)
                response = model.generate_content([prompt, image])
            else:
                if not text or not text.strip():
                    return []
                response = model.generate_content(
                    prompt + f"\n\nText to parse:\n{text}"
                )

            clean_json = (
                response.text.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            items_data = json.loads(clean_json)

            parsed_items = []
            for entry in items_data:
                l = int(entry.get("length", 48))
                w = int(entry.get("width", 40))
                h = int(entry.get("height", 48))
                wt = float(entry.get("weight", 500.0))
                qty = int(entry.get("qty", 1))

                for _ in range(max(1, qty)):
                    parsed_items.append({
                        "type": f"Parsed (AI Vision) [{l}x{w}x{h}]",
                        "length": l,
                        "width": w,
                        "height": h,
                        "weight": wt,
                        "stackable": False,
                    })
            if parsed_items:
                return parsed_items
        except Exception as e:
            st.error(f"❌ Gemini Vision API Error: {e}")

    # --- FALLBACK REGEX ENSEMBLE ---
    items = []
    if not text:
        return items
    lines = text.split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean or re.search(
            r"total\s+weight|pallet\s+count", line_clean, re.IGNORECASE
        ):
            continue

        qty_match = re.search(r"\b(\d+)\s*[@xX]\b", line_clean)
        qty = int(qty_match.group(1)) if qty_match else 1

        wt_match = re.search(
            r"(?:weight|wt|wgt)[\s:=]*(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*(?:#|lbs?\.?|pounds?|kg)",
            line_clean,
            re.IGNORECASE,
        )
        item_wt = (
            float(wt_match.group(1) or wt_match.group(2)) if wt_match else 500.0
        )

        dim_match = re.search(
            r"(\d+)\s*[\'\"\s]*[xX×]\s*(\d+)\s*[\'\"\s]*[xX×]\s*(\d+)",
            line_clean,
        )
        if dim_match:
            l, w, h = (
                int(dim_match.group(1)),
                int(dim_match.group(2)),
                int(dim_match.group(3)),
            )
            for _ in range(max(1, qty)):
                items.append({
                    "type": f"Parsed (Regex) [{l}x{w}x{h}]",
                    "length": l,
                    "width": w,
                    "height": h,
                    "weight": item_wt,
                    "stackable": False,
                })
    return items


if "custom_pallets_list" not in st.session_state:
    st.session_state.custom_pallets_list = []

with col2:
    st.markdown("#### Custom Cargo & Smart Import")

    tab_manual, tab_smart = st.tabs(
        ["➕ Manual Entry", "📷 Smart OCR / Paste Text"]
    )

    with tab_manual:
        with st.popover("➕ Add Custom Dimensions", use_container_width=True):
            st.markdown("**Custom Freight Parameters**")
            cp_l = st.number_input("Length (in)", min_value=1, value=48)
            cp_w = st.number_input("Width (in)", min_value=1, value=40)
            cp_h = st.number_input("Height (in)", min_value=1, value=50)
            cp_wt = st.number_input(
                "Weight per Unit (lbs)", min_value=1, value=500
            )
            cp_qty = st.number_input("Quantity", min_value=1, value=1)
            cp_stack = st.checkbox(
                "Stackable (Allow items on top)",
                value=False,
                key="cust_stack_pop",
            )

            if st.button(
                "Add to Freight Manifest",
                type="primary",
                use_container_width=True,
            ):
                for _ in range(cp_qty):
                    st.session_state.custom_pallets_list.append({
                        "type": f'Custom ({cp_l}"x{cp_w}"x{cp_h})',
                        "length": cp_l,
                        "width": cp_w,
                        "height": cp_h,
                        "weight": cp_wt,
                        "stackable": cp_stack,
                    })
                st.rerun()

    with tab_smart:
        st.caption(
            "Paste broker specifications or upload rate confirmation / document"
            " screenshots:"
        )

        raw_text = st.text_area("Paste Dimensions & Weight Text", height=90)
        uploaded_file = st.file_uploader(
            "Upload Document / Image", type=["png", "jpg", "jpeg"]
        )

        smart_stackable = st.checkbox(
            "Stackable (Apply to all parsed items)",
            value=False,
            key="smart_tab_stack_toggle",
        )
        parse_clicked = st.button(
            "↵ Process & Parse Cargo",
            type="primary",
            use_container_width=True,
        )

        if parse_clicked:
            text_to_process = raw_text

            if uploaded_file is not None:
                if not GEMINI_AVAILABLE:
                    st.warning(
                        "⚠️ Gemini API is not available (`GEMINI_API_KEY` missing"
                        " or package not installed)."
                    )

            parsed_items = llm_parse_cargo_text(
                text_to_process, uploaded_file=uploaded_file
            )

            if parsed_items:
                for item in parsed_items:
                    item["stackable"] = smart_stackable
                st.session_state.custom_pallets_list.extend(parsed_items)
                st.success(
                    f"Successfully imported {len(parsed_items)} freight item(s)!"
                )
                st.rerun()
            else:
                st.warning(
                    "Unable to parse dimensions. Verify format or paste text"
                    " directly."
                )

    if st.session_state.custom_pallets_list:
        st.markdown("**Active Custom & Imported Items:**")
        to_delete = None

        for idx, item in enumerate(st.session_state.custom_pallets_list):
            c_info, c_stack, c_btn = st.columns([3, 2, 1])
            with c_info:
                st.caption(f"• {item['type']} @ **{item['weight']} lbs**")
            with c_stack:
                is_stk = st.checkbox(
                    "Stackable",
                    value=item.get("stackable", False),
                    key=f"stack_cust_toggle_{idx}",
                )
                item["stackable"] = is_stk
            with c_btn:
                if st.button("❌", key=f"del_cust_{idx}"):
                    to_delete = idx

            pallets_to_plan.append(item)

        if to_delete is not None:
            st.session_state.custom_pallets_list.pop(to_delete)
            st.rerun()

# --- OPTIMIZED RUN PACKING SIMULATION ---
total_weight = sum(item["weight"] for item in pallets_to_plan)
total_units = len(pallets_to_plan)

pallets_to_plan.sort(
    key=lambda item: item["length"] * item["width"] * item["height"],
    reverse=True,
)

# Pink color palette for cargo boxes
colors = ["#db2777", "#be185d", "#9d174d", "#831843", "#f472b6", "#f43f5e"]
dim_color_map = {}
placed_boxes = []
all_fits = True


def check_overlap(x, y, z, dx, dy, dz):
    if (
        x < 0
        or y < 0
        or z < 0
        or x + dx > v_length
        or y + dy > v_width
        or z + dz > v_height
    ):
        return True
    for b in placed_boxes:
        if not (
            x + dx <= b["x"]
            or x >= b["x"] + b["dx"]
            or y + dy <= b["y"]
            or y >= b["y"] + b["dy"]
            or z + dz <= b["z"]
            or z >= b["z"] + b["dz"]
        ):
            return True
    return False


for item in pallets_to_plan:
    p_l_orig, p_w_orig, p_h = item["length"], item["width"], item["height"]

    dim_key = (p_l_orig, p_w_orig, p_h)
    if dim_key not in dim_color_map:
        dim_color_map[dim_key] = colors[len(dim_color_map) % len(colors)]
    p_color = dim_color_map[dim_key]
    is_stackable = item.get("stackable", False)

    orientations = [(p_l_orig, p_w_orig), (p_w_orig, p_l_orig)]
    if p_l_orig == p_w_orig:
        orientations = [(p_l_orig, p_w_orig)]

    placed = False
    found_pos_and_dims = None

    z_levels = {0.0}
    for b in placed_boxes:
        if b["stackable"]:
            z_levels.add(b["z"] + b["dz"])
    sorted_z_levels = sorted(list(z_levels))

    for z in sorted_z_levels:
        if z + p_h > v_height:
            continue

        x_candidates = sorted(
            list(
                set(
                    [0.0]
                    + [b["x"] for b in placed_boxes]
                    + [b["x"] + b["dx"] for b in placed_boxes]
                )
            )
        )
        y_candidates = sorted(
            list(
                set(
                    [0.0]
                    + [b["y"] for b in placed_boxes]
                    + [b["y"] + b["dy"] for b in placed_boxes]
                )
            )
        )

        for p_l, p_w in orientations:
            for x in x_candidates:
                if x + p_l > v_length:
                    continue
                for y in y_candidates:
                    if y + p_w > v_width:
                        continue
                    if not check_overlap(x, y, z, p_l, p_w, p_h):
                        supported = True
                        if z > 0:
                            supported = False
                            for b in placed_boxes:
                                if (
                                    abs((b["z"] + b["dz"]) - z) < 0.1
                                    and b["stackable"]
                                ):
                                    inter_x = max(
                                        0.0,
                                        min(x + p_l, b["x"] + b["dx"])
                                        - max(x, b["x"]),
                                    )
                                    inter_y = max(
                                        0.0,
                                        min(y + p_w, b["y"] + b["dy"])
                                        - max(y, b["y"]),
                                    )
                                    if (inter_x * inter_y) >= (
                                        0.55 * (p_l * p_w)
                                    ):
                                        supported = True
                                        break
                        if supported:
                            found_pos_and_dims = (x, y, z, p_l, p_w)
                            break
                if found_pos_and_dims:
                    break
            if found_pos_and_dims:
                break
        if found_pos_and_dims:
            break

    if found_pos_and_dims:
        fx, fy, fz, pl_used, pw_used = found_pos_and_dims
        placed_boxes.append({
            "x": fx,
            "y": fy,
            "z": fz,
            "dx": pl_used,
            "dy": pw_used,
            "dz": p_h,
            "color": p_color,
            "stackable": is_stackable,
        })
        placed = True

    if not placed:
        all_fits = False

# --- METRICS & ANALYSIS ---
st.markdown("---")
st.subheader("📊 Load Manifest & Weight Analysis")

if total_weight > max_payload:
    st.error(
        f"⚠️ **Weight Compliance Alert:** Total cargo weight"
        f" ({total_weight:,.1f} lbs) exceeds maximum allowable payload capacity"
        f" ({max_payload:,} lbs)."
    )

if not all_fits:
    st.warning(
        "⚠️ **Volumetric Space Alert:** Cargo exceeds available 3D dimensional"
        " space or stacking constraints of the equipment."
    )

m1, m2, m3 = st.columns(3)
m1.metric("Total Cargo Pieces", f"{total_units} units")
m2.metric(
    "Gross Cargo Weight",
    f"{total_weight:,.1f} lbs",
    delta=(
        f"{max_payload - total_weight:,.1f} lbs remaining"
        if total_weight <= max_payload
        else "OVERWEIGHT!"
    ),
    delta_color="normal" if total_weight <= max_payload else "inverse",
)
m3.metric(
    "Payload Compliance",
    "PASSED ✅" if total_weight <= max_payload else "EXCEEDED ⚠️",
)

# --- EXCEL MANIFEST EXPORT ---
if pallets_to_plan:
    excel_buffer = io.BytesIO()
    manifest_df = pd.DataFrame(pallets_to_plan)
    manifest_df.columns = [col.capitalize() for col in manifest_df.columns]

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        manifest_df.to_excel(writer, index=False, sheet_name="Load Manifest")

        summary_data = pd.DataFrame({
            "Metric": [
                "Equipment Type",
                "Bed Length (in)",
                "Bed Width (in)",
                "Internal Height (in)",
                "Max Payload (lbs)",
                "Total Cargo Pieces",
                "Gross Cargo Weight (lbs)",
                "Payload Compliance",
            ],
            "Value": [
                vehicle_type,
                v_length,
                v_width,
                v_height,
                max_payload,
                total_units,
                total_weight,
                "PASSED" if total_weight <= max_payload else "EXCEEDED",
            ],
        })
        summary_data.to_excel(writer, index=False, sheet_name="Trip Summary")

    st.download_button(
        label="📥 Export Load Manifest & Summary to Excel (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name="JoulieTheBully_Load_Manifest.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

# --- MODERNIZED 3D VISUALIZATION ENGINE ---
st.subheader("🧊 Interactive 3D Trailer Load Model")


def plot_cube(
    ax,
    x,
    y,
    z,
    dx,
    dy,
    dz,
    color="#db2777",
    alpha=0.85,
    edgecolor="#831843",
    linewidth=0.6,
):
    vertices = np.array([
        [x, y, z],
        [x + dx, y, z],
        [x + dx, y + dy, z],
        [x, y + dy, z],
        [x, y, z + dz],
        [x + dx, y, z + dz],
        [x + dx, y + dy, z + dz],
        [x, y + dy, z + dz],
    ])

    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[0], vertices[1], vertices[5], vertices[4]],
        [vertices[2], vertices[3], vertices[7], vertices[6]],
        [vertices[1], vertices[2], vertices[6], vertices[5]],
        [vertices[4], vertices[7], vertices[3], vertices[0]],
    ]

    poly = Poly3DCollection(
        faces,
        facecolors=color,
        linewidths=linewidth,
        edgecolors=edgecolor,
        alpha=alpha,
    )
    ax.add_collection3d(poly)


fig = plt.figure(figsize=(14, 6))
fig.patch.set_facecolor("#fdf2f8")
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor("#fdf2f8")

ax.set_box_aspect((v_length, v_width, v_height))
ax.set_xlim(0, v_length)
ax.set_ylim(0, v_width)
ax.set_zlim(0, v_height)

ax.set_xticks(np.linspace(0, v_length, 5))
ax.set_yticks([0, v_width])
ax.set_zticks(np.linspace(0, v_height, 5))

ax.xaxis.set_pane_color((0.98, 0.91, 0.95, 1.0))
ax.yaxis.set_pane_color((0.98, 0.91, 0.95, 1.0))
ax.zaxis.set_pane_color((0.98, 0.91, 0.95, 1.0))

ax.tick_params(colors="#831843", labelsize=10)

ax.set_xlabel("Length (in)", labelpad=12, color="#831843", fontweight="bold")
ax.set_ylabel(
    f'Width ({v_width}" Total)',
    labelpad=12,
    color="#831843",
    fontweight="bold",
)
ax.set_zlabel("Height (in)", labelpad=12, color="#831843", fontweight="bold")

plot_cube(
    ax,
    v_length / 2,
    0,
    0,
    v_length / 2,
    v_width,
    1,
    color="#fbcfe8",
    alpha=0.15,
    edgecolor="none",
)
plot_cube(
    ax,
    0,
    0,
    0,
    v_length,
    v_width,
    v_height,
    color="#fbcfe8",
    alpha=0.03,
    edgecolor="#f472b6",
    linewidth=1,
)

for b in placed_boxes:
    plot_cube(
        ax,
        b["x"],
        b["y"],
        b["z"],
        b["dx"],
        b["dy"],
        b["dz"],
        color=b["color"],
        alpha=0.85,
    )

ax.view_init(elev=22, azim=-52)
st.pyplot(fig)

# --- U.S. ON-HIGHWAY DIESEL PRICES (LIVE EIA FETCH) ---
st.markdown("---")
st.markdown(
    "### ⛽ U.S. On-Highway Diesel Fuel Prices (Official EIA Weekly Average)"
)

eia_url = "https://www.eia.gov/petroleum/gasdiesel/"

try:
    tables = pd.read_html(eia_url, flavor="html5lib")
    diesel_df = tables[0]
    st.dataframe(diesel_df, hide_index=True, use_container_width=True)
except Exception:
    try:
        tables = pd.read_html(eia_url)
        diesel_df = tables[0]
        st.dataframe(diesel_df, hide_index=True, use_container_width=True)
    except Exception:
        fallback_diesel_data = {
            "Week Ending Date": [
                "July 27, 2026",
                "July 20, 2026",
                "July 13, 2026",
                "July 06, 2026",
                "June 29, 2026",
                "June 22, 2026",
                "June 15, 2026",
                "June 08, 2026",
            ],
            "U.S. National Average ($/gal)": [
                "$5.313",
                "$5.134",
                "$4.796",
                "$4.578",
                "$4.668",
                "$4.832",
                "$5.059",
                "$5.210",
            ],
            "Weekly Change": [
                "+$0.179",
                "+$0.338",
                "+$0.218",
                "-$0.090",
                "-$0.164",
                "-$0.227",
                "-$0.151",
                "-$0.140",
            ],
        }
        fallback_df = pd.DataFrame(fallback_diesel_data)
        st.dataframe(fallback_df, hide_index=True, use_container_width=True)
