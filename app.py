import streamlit as st
import gspread
import traceback
import os
import re
import json
from datetime import date
from PIL import Image

# 1. Konfigurasi Tampilan Web Form
st.set_page_config(
    page_title="Dashboard Input OEE, MTTR & Material Control", 
    page_icon="🍦", 
    layout="centered"
)

# Mencegah rekomendasi autofill popup dari browser
st.markdown("""
    <style>
        input {
            autocomplete: off;
        }
    </style>
""", unsafe_allow_html=True)

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

st.info("💡 **Tips Input:** Pilih produk terdaftar untuk mengisi berat secara otomatis. Kolom angka mendukung rumus seperti `85+5` atau `1/342`. Jika tidak ada produksi (libur), semua kolom angka bisa diisi `0`.")
st.divider()

SPREADSHEET_ID = "1jrIXnAY4NiVpxL3mPHjhZx5b3hrEbZwFKIeHrL1b4C8"

# Database Kamus Produk & Berat Standar (gram)
PRODUCT_DATABASE = {
    "CCL": "36",
    "CCM": "39",
    "CVC": "39",
    "CVB": "35",
    "Cool Strawberry": "56",
    "CWA": "41",
    "Milky Milk": "35",
    "Kokomi": "23",
    "Lalava": "23",
    "Tropical Duo": "45",
    "Frutty Duo": "45",
    "Galaxy": "47",
    "Choco Barry": "40",
    "Es Susu": "35",
    "Choco Fun": "35",
    "Choco Crunch": "31",
    "Guava": "50",
    "Catton Candy": "45",
    "Choco Malt": "38",
}

# 4. Fungsi Validasi Real-Time (Mendukung Input 0 & Pembagian Nol)
def validate_realtime(expression, field_name):
    if expression is None or str(expression).strip() == "":
        return True, "", 0.0

    expr_str = str(expression).strip()

    if re.search(r'[a-zA-Z]', expr_str):
        return False, f"⚠️ **{field_name}** mengandung huruf (`{expr_str}`). Harap isi dengan angka/rumus yang sesuai!", None

    clean_expr = expr_str.replace(",", ".")

    try:
        if re.match(r'^[0-9\.\+\-\*\/\(\)\s]+$', clean_expr):
            val = float(eval(clean_expr, {"__builtins__": None}, {}))
            return True, "", val
        else:
            return False, f"⚠️ Penulisan rumus pada **{field_name}** ({expr_str}) tidak valid!", None
    except ZeroDivisionError:
        return True, "", 0.0
    except Exception:
        return False, f"⚠️ Penulisan rumus pada **{field_name}** ({expr_str}) tidak valid!", None

# 5. Fungsi Koneksi Google Sheets
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

# --- AREA INPUT FORM ---
with st.form(key="oee_input_form", clear_on_submit=True):
    st.subheader("📌 Informasi Produk & Area")
    col1, col2 = st.columns(2)

    with col1:
        tgl = st.date_input("Tanggal Produksi", value=date.today())
        
        product_options = list(PRODUCT_DATABASE.keys()) + ["Other (Lainnya...)"]
        selected_product = st.selectbox("Nama Produk", options=product_options)
        
        if selected_product == "Other (Lainnya...)":
            custom_product_name = st.text_input("Ketik Nama Produk Baru", placeholder="Ketik nama produk baru...")
            default_weight = "0"
        else:
            custom_product_name = ""
            default_weight = PRODUCT_DATABASE[selected_product]

    with col2:
        line = st.selectbox("Line Production", [f"Line {i}" for i in range(1, 7)])
        berat_produk_raw = st.text_input("Berat Produk (gram)", value=default_weight, key=f"berat_{selected_product}")

    st.subheader("⏱️ Waktu Operasional & Downtime (Menit)")
    col3, col4, col5 = st.columns(3)

    with col3:
        downtime_unplanned_raw = st.text_input("Downtime Tidak Terencana", value="0", help="Contoh: 30+15+10 atau 0")

    with col4:
        planned_downtime_raw = st.text_input("Planned Downtime", value="0", help="Contoh: 60+60 atau 0")

    with col5:
        cycle_time_raw = st.text_input("Waktu Siklus Ideal", value="0", help="Contoh: 0.05, 1/342, atau 0")

    st.subheader("📦 Output Produksi & Waste Material (Pcs)")
    col6, col7, col8 = st.columns(3)

    with col6:
        total_output_raw = st.text_input("Output Produksi", value="0", help="Contoh: (1000*10)+(500*2) atau 0")

    with col7:
        defect_prod_raw = st.text_input("Defect Produksi", value="0", help="Contoh: 50+25 atau 0")

    with col8:
        waste_stick_raw = st.text_input("Waste Stick", value="0", help="Contoh: 100+40 atau 0")

    st.markdown("---")
    submit_button = st.form_submit_button("🚀 Simpan Data Laporan", use_container_width=True)

# 6. Eksekusi Validasi Rumus & Simpan Data Saat Tombol Diklik
if submit_button:
    # Lakukan validasi rumus saat tombol simpan diklik
    is_valid_berat, err_berat, val_berat = validate_realtime(berat_produk_raw, "Berat Produk")
    is_valid_dtu, err_dtu, val_dt_unplanned = validate_realtime(downtime_unplanned_raw, "Downtime Tidak Terencana")
    is_valid_dtp, err_dtp, val_dt_planned = validate_realtime(planned_downtime_raw, "Planned Downtime")
    is_valid_ct, err_ct, val_cycle_time = validate_realtime(cycle_time_raw, "Waktu Siklus Ideal")
    is_valid_out, err_out, val_output = validate_realtime(total_output_raw, "Output Produksi")
    is_valid_def, err_def, val_defect = validate_realtime(defect_prod_raw, "Defect Produksi")
    is_valid_wst, err_wst, val_waste = validate_realtime(waste_stick_raw, "Waste Stick")

    # Kumpulkan daftar error jika ada penulisan rumus yang salah
    errors = [err for is_v, err, _ in [
        (is_valid_berat, err_berat, val_berat),
        (is_valid_dtu, err_dtu, val_dt_unplanned),
        (is_valid_dtp, err_dtp, val_dt_planned),
        (is_valid_ct, err_ct, val_cycle_time),
        (is_valid_out, err_out, val_output),
        (is_valid_def, err_def, val_defect),
        (is_valid_wst, err_wst, val_waste)
    ] if not is_v]

    if errors:
        for err in errors:
            st.error(err)
        st.warning("⚠️ Silakan perbaiki kesalahan penulisan rumus di atas sebelum menyimpan data.")
    else:
        if selected_product == "Other (Lainnya...)":
            final_product_name = custom_product_name.strip()
        else:
            final_product_name = selected_product

        if not final_product_name:
            st.error("⚠️ **Nama Produk** wajib diisi/diketik jika memilih Other!")
        else:
            try:
                with st.spinner("Menghitung rumus & menyimpan data ke Google Sheets..."):
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