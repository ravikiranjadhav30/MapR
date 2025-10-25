import streamlit as st
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import folium
from streamlit_folium import st_folium
import base64

# ---------- CONFIG ----------
st.set_page_config(page_title="GeoTagged Image Map", layout="wide")
DATA_DIR = "uploaded_images"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- ADMIN CREDENTIALS ----------
ADMIN_USERNAME = "Ravikiran"
ADMIN_PASSWORD = "30111997"

# ---------- APP STATE ----------
auth_status = st.session_state.get("authenticated", False)
menu = ["Public Viewer", "Admin Login", "Logout"]
choice = st.sidebar.selectbox("Navigation", menu)

# ---------- LOGOUT ----------
if choice == "Logout":
    st.session_state["authenticated"] = False
    st.success("Logged out successfully ✅")

# ---------- HELPER FUNCTIONS ----------
def get_exif_data(image):
    """Extract EXIF data from an image"""
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
    except:
        pass
    return exif_data

def get_gps_info(exif_data):
    """Extract GPS coordinates in decimal format"""
    gps_info = {}
    if "GPSInfo" in exif_data:
        for key in exif_data["GPSInfo"].keys():
            decode = GPSTAGS.get(key,key)
            gps_info[decode] = exif_data["GPSInfo"][key]
        # Convert to decimal
        def convert_to_decimal(coord, ref):
            decimal = coord[0] + coord[1]/60 + coord[2]/3600
            if ref in ['S','W']:
                decimal = -decimal
            return decimal
        try:
            lat = convert_to_decimal(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
            lon = convert_to_decimal(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])
            return lat, lon
        except:
            return None, None
    return None, None

def image_to_base64(img_path):
    """Convert image to base64 for embedding in HTML"""
    with open(img_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ---------- ADMIN LOGIN ----------
if choice == "Admin Login":
    if not auth_status:
        st.subheader("🔑 Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.success("✅ Login successful")
            else:
                st.error("❌ Invalid credentials")
    else:
        st.subheader("📤 Upload GeoTagged Images")
        uploaded_file = st.file_uploader("Upload Image (.png/.jpg)", type=["png","jpg","jpeg"])
        if uploaded_file:
            save_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")

        st.markdown("### 🗑️ Delete Existing Files")
        files = os.listdir(DATA_DIR)
        if files:
            file_to_delete = st.selectbox("Select file to delete", files)
            if st.button("Delete File"):
                os.remove(os.path.join(DATA_DIR, file_to_delete))
                st.warning(f"🗑️ {file_to_delete} deleted successfully!")
        else:
            st.info("No images available to delete.")

# ---------- PUBLIC VIEWER ----------
if choice == "Public Viewer":
    st.subheader("🛰️ GeoTagged Image Map")
    files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith((".png",".jpg",".jpeg"))]
    m = folium.Map(location=[19.0, 75.0], zoom_start=6, tiles="OpenStreetMap")

    if files:
        for file in files:
            path = os.path.join(DATA_DIR, file)
            try:
                img = Image.open(path)
                exif_data = get_exif_data(img)
                lat, lon = get_gps_info(exif_data)
                if lat and lon:
                    img_base64 = image_to_base64(path)
                    html = f"""
                    <b>{file}</b><br>
                    <img src="data:image/jpeg;base64,{img_base64}" width="150">
                    """
                    folium.Marker(
                        location=[lat, lon],
                        popup=folium.Popup(html, max_width=200),
                        icon=folium.Icon(color='red', icon='camera')
                    ).add_to(m)
            except Exception as e:
                st.warning(f"Failed to process {file}: {e}")
        folium.LayerControl().add_to(m)
        st_folium(m, width=900, height=600)
    else:
        st.info("No geo-tagged images available. Please upload via Admin Login.")
