import streamlit as st
import gspread
import traceback
import os
import json
from datetime import date
from PIL import Image

# 1. Konfigurasi Tampilan Web Form
st.set_page_config(
    page_title="Dashboard Input OEE, MTTR & Material Control", 
    page_icon="🍦", 
    layout="centered"
)

# 2. Menampilkan Logo PT Green Asia Food Indonesia (Yili Group)
col1_logo, col2_logo, col3_logo = st.columns([1, 2, 1])
with col2_logo:
    logo_found = False
    possible_filenames = [
        'yili_joyday.png', 'yili_joyday.jpg', 'yili_joyday.jpeg',
        'yili_joyday.PNG', 'yili_joyday.JPG', 'yili_joyday.JPEG'
    ]
    for filename in possible_filenames:
        if os.path.exists(filename):
            try:
                logo = Image.open(filename)
                st.image(logo, width=1200)
                logo_found = True
                break
            except Exception:
                pass

    if not logo_found:
        st.warning("⚠️ File logo 'yili_joyday' tidak ditemukan di folder proyek!")

# 3. Judul Utama Aplikasi
st.markdown(
    """
    <h2 style='text-align: center; color: #1E293B; font-weight: 700; margin-bottom: 5px; font-size: 40px;'>
        🍦 Dashboard Input Data OEE, MTTR & Material Control
    </h2>
    <p style='text-align: center; color: #64748B; font-size: 14px; margin-bottom: 25px;'>
        Form Rekap Harian: Kinerja Line Produksi, Downtime, Output & Waste Stick Ice Cream
    </p>
    """, 
    unsafe_allow_html=True
)

st.info("💡 **Tips Input:** Isi data sesuai laporan harian. Setelah klik simpan, semua kolom angka akan otomatis ter-reset kembali ke angka 0.")
st.divider()

SPREADSHEET_ID = "1jrIXnAY4NiVpxL3mPHjhZx5b3hrEbZwFKIeHrL1b4C8"

PRODUCT_DATABASE = {
    "CCL": 36.0, "CCM": 39.0, "CVC": 39.0, "CVB": 35.0,
    "Cool Strawberry": 56.0, "CWA": 41.0, "Milky Milk": 35.0,
    "Kokomi": 23.0, "Lalava": 23.0, "Tropical Duo": 45.0,
    "Frutty Duo": 45.0, "Galaxy": 47.0, "Choco Barry": 40.0,
    "Es Susu": 35.0, "Choco Fun": 35.0, "Choco Crunch": 31.0,
    "Guava": 50.0, "Catton Candy": 45.0, "Choco Malt": 38.0,
}

def get_sheet():
    if "GCP_JSON" in st.secrets:
        creds_dict = json.loads(st.secrets["GCP_JSON"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        gc = gspread.service_account_from_dict(creds_dict)
    elif "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        gc = gspread.service_account(
            filename="golden-index-510211-i4-5bc3df8a2ee9.json"
        )
    return gc.open_by_key(SPREADSHEET_ID).worksheet("Data_Harian")

# --- AREA INPUT FORM BERSUIH & TANPA WARNING ---
with st.form(key="oee_input_form", clear_on_submit=True):
    st.subheader("📌 Informasi Produk & Area")
    col1, col2 = st.columns(2)

    with col1:
        tgl = st.date_input("Tanggal Produksi", value=date.today())
        
        product_options = list(PRODUCT_DATABASE.keys()) + ["Other (Lainnya...)"]
        selected_product = st.selectbox("Nama Produk", options=product_options)
        
        if selected_product == "Other (Lainnya...)":
            custom_product_name = st.text_input("Ketik Nama Produk Baru", placeholder="Ketik nama produk baru...")
            default_weight = 0.0
        else:
            custom_product_name = ""
            default_weight = PRODUCT_DATABASE[selected_product]

    with col2:
        line = st.selectbox("Line Production", [f"Line {i}" for i in range(1, 7)])
        val_berat = st.number_input("Berat Produk (gram)", min_value=0.0, value=default_weight, step=1.0)

    st.subheader("⏱️ Waktu Operasional & Downtime (Menit)")
    col3, col4, col5 = st.columns(3)

    with col3:
        val_dt_unplanned = st.number_input("Downtime Tidak Terencana", min_value=0, value=0, step=1)

    with col4:
        val_dt_planned = st.number_input("Planned Downtime", min_value=0, value=0, step=1)

    with col5:
        val_cycle_time = st.number_input("Waktu Siklus Ideal", min_value=0.0, value=0.0, format="%.4f")

    st.subheader("📦 Output Produksi & Waste Material (Pcs)")
    col6, col7, col8 = st.columns(3)

    with col6:
        val_output = st.number_input("Output Produksi", min_value=0, value=0, step=1)

    with col7:
        val_defect = st.number_input("Defect Produksi", min_value=0, value=0, step=1)

    with col8:
        val_waste = st.number_input("Waste Stick", min_value=0, value=0, step=1)

    st.markdown("---")
    submit_button = st.form_submit_button("🚀 Simpan Data Laporan", use_container_width=True)

# Eksekusi Simpan Data
if submit_button:
    if selected_product == "Other (Lainnya...)" and not custom_product_name.strip():
        st.error("⚠️ **Nama Produk** wajib diketik jika memilih Other!")
    else:
        final_product_name = custom_product_name.strip() if selected_product == "Other (Lainnya...)" else selected_product
        try:
            with st.spinner("Menyimpan data ke Google Sheets..."):
                sheet = get_sheet()
                new_row = [
                    str(tgl),
                    str(line),
                    str(final_product_name),
                    val_berat,
                    int(val_dt_unplanned),
                    int(val_dt_planned),
                    int(val_output),
                    int(val_defect),
                    val_cycle_time,
                    int(val_waste)
                ]
                sheet.append_row(new_row, value_input_option="USER_ENTERED")
            
            st.success(f"✅ Data tanggal {tgl} untuk {line} ({final_product_name}) berhasil disimpan!")

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat menyimpan data: {e}")
            st.code(traceback.format_exc(), language="python")