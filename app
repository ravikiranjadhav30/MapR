import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import rasterio
import numpy as np
from PIL import Image
from folium.raster_layers import ImageOverlay

# ---------- CONFIG ----------
st.set_page_config(page_title="GeoTIFF Map Viewer", layout="wide")

DATA_DIR = "uploaded_tiffs"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- APP TITLE ----------
st.title("🗺️ Web-based GeoTIFF Map Application")

# ---------- ADMIN LOGIN ----------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"
auth_status = st.session_state.get("authenticated", False)

menu = ["Public Viewer", "Admin Login", "Logout"]
choice = st.sidebar.selectbox("Navigation", menu)

# ---------- LOGOUT ----------
if choice == "Logout":
    st.session_state["authenticated"] = False
    st.success("You have been logged out.")

# ---------- ADMIN PANEL ----------
if choice == "Admin Login":
    if not auth_status:
        st.subheader("🔑 Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.success("✅ Login successful!")
            else:
                st.error("❌ Invalid username or password")
    else:
        st.subheader("📤 Upload or Delete GeoTIFF Files")

        uploaded_file = st.file_uploader("Upload a GeoTIFF file", type=["tif", "tiff"])
        if uploaded_file:
            file_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")

        st.markdown("### 🗑️ Delete Existing Files")
        existing_files = os.listdir(DATA_DIR)
        if existing_files:
            file_to_delete = st.selectbox("Select file to delete", existing_files)
            if st.button("Delete File"):
                os.remove(os.path.join(DATA_DIR, file_to_delete))
                st.warning(f"🗑️ {file_to_delete} deleted successfully!")
        else:
            st.info("No files available to delete.")

# ---------- PUBLIC VIEWER ----------
if choice == "Public Viewer":
    st.subheader("🛰️ Public Map Viewer")

    m = folium.Map(location=[19.0, 75.0], zoom_start=6, tiles="OpenStreetMap")

    tif_files = [f for f in os.listdir(DATA_DIR) if f.endswith((".tif", ".tiff"))]

    if tif_files:
        selected_tif = st.selectbox("Select a GeoTIFF layer to view:", tif_files)

        if selected_tif:
            file_path = os.path.join(DATA_DIR, selected_tif)
            if os.path.exists(file_path):
                with rasterio.open(file_path) as src:
                    bounds = src.bounds
                    array = src.read(1)
                    array = np.nan_to_num(array)
                    norm = (array - array.min()) / (array.max() - array.min())
                    img = Image.fromarray(np.uint8(norm * 255))
                    img.save("temp.png")

                    img_overlay = ImageOverlay(
                        name=selected_tif,
                        image="temp.png",
                        bounds=[[bounds.bottom, bounds.left],
                                [bounds.top, bounds.right]],
                        opacity=0.6,
                    )
                    img_overlay.add_to(m)

                folium.LayerControl().add_to(m)
                st_folium(m, width=900, height=600)
            else:
                st.error(f"⚠️ File not found: {file_path}")
    else:
        st.info("No GeoTIFF files available. Please upload via Admin Login.")
