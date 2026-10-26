import os
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from sqlalchemy import create_engine
import streamlit as st

# --- CONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(
    page_title="E-Commerce Customer Satisfaction Dashboard",
    page_icon="🛒",
    layout="wide",
)


# --- KONEKSI DATABASE (AMBIL DARI SECRETS / ENV) ---
@st.cache_resource
def init_connections():
    # Ambil credentials dari Streamlit Secrets / Environment Variable
    supabase_url = st.secrets.get(
        "SUPABASE_URL", os.getenv("SUPABASE_URL", "")
    )
    mongo_uri = st.secrets.get("MONGO_URI", os.getenv("MONGO_URI", ""))

    engine = create_engine(supabase_url)
    mongo_client = MongoClient(mongo_uri)
    return engine, mongo_client


# --- DATA PIPELINE (FEDERATION / MERGE) ---
@st.cache_data(ttl=600)
def load_and_merge_data():
    engine, mongo_client = init_connections()

    # 1. Tarik Data Relasional dari Supabase
    df_orders = pd.read_sql("SELECT * FROM orders", engine)
    df_customers = pd.read_sql("SELECT * FROM customers", engine)

    # 2. Tarik Data Document/NoSQL dari MongoDB Atlas
    db = mongo_client["olist_db"]
    df_reviews = pd.DataFrame(list(db["reviews"].find({}, {"_id": 0})))
    df_payments = pd.DataFrame(list(db["payments"].find({}, {"_id": 0})))

    # 3. Data Joining / Federation di Tingkat Aplikasi
    df_merged = df_orders.merge(df_customers, on="customer_id", how="inner")
    df_merged = df_merged.merge(df_reviews, on="order_id", how="left")
    df_merged = df_merged.merge(df_payments, on="order_id", how="left")

    return df_merged


# --- LOAD DATA ---
try:
    df = load_and_merge_data()
except Exception as e:
    st.error(
        f"Gagal menghubungkan ke database. Pastikan Secrets sudah diatur! Error: {e}"
    )
    st.stop()

# --- HEADER & DESKRIPSI ARSITEKTUR ---
st.title("🛒 E-Commerce Customer Satisfaction & Order Analytics")
st.markdown("""
*Multi-DBMS Data Pipeline Dashboard* yang mengintegrasikan data dari dua sistem basis data berbeda:
- **Supabase (PostgreSQL - Relational):** Menyimpan data utama pesanan (`orders`) dan pelanggan (`customers`).
- **MongoDB Atlas (NoSQL - Document Store):** Menyimpan log ulasan (`reviews`) dan metode pembayaran (`payments`).
""")

# --- SIDEBAR FILTER ---
st.sidebar.header("🔍 Filter Data")

status_list = ["Semua"] + list(df["order_status"].dropna().unique())
selected_status = st.sidebar.selectbox("Pilih Status Pesanan:", status_list)

payment_list = ["Semua"] + list(df["payment_type"].dropna().unique())
selected_payment = st.sidebar.selectbox(
    "Pilih Metode Pembayaran:", payment_list
)

# Apply Filter
df_filtered = df.copy()
if selected_status != "Semua":
    df_filtered = df_filtered[df_filtered["order_status"] == selected_status]
if selected_payment != "Semua":
    df_filtered = df_filtered[df_filtered["payment_type"] == selected_payment]

# --- RINGKASAN METRIK (KPI) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pesanan", f"{len(df_filtered):,}")
col2.metric("Rata-rata Rating Score", f"{df_filtered['review_score'].mean():.2f} ⭐")
col3.metric(
    "Total Pembayaran ($)", f"${df_filtered['payment_value'].sum():,.2f}"
)
col4.metric(
    "Rata-rata Nilai Order ($)", f"${df_filtered['payment_value'].mean():,.2f}"
)

st.markdown("---")

# --- VISUALISASI DATA ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Distribusi Skor Rating Ulasan")
    df_rating = (
        df_filtered["review_score"].value_counts().reset_index()
    )
    df_rating.columns = ["review_score", "count"]
    fig_rating = px.bar(
        df_rating,
        x="review_score",
        y="count",
        labels={"review_score": "Skor Rating (1-5)", "count": "Jumlah Transaksi"},
        color="review_score",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig_rating, use_container_width=True)

with col_right:
    st.subheader("💳 Proporsi Metode Pembayaran")
    df_payment = (
        df_filtered["payment_type"].value_counts().reset_index()
    )
    df_payment.columns = ["payment_type", "count"]
    fig_payment = px.pie(
        df_payment,
        values="count",
        names="payment_type",
        hole=0.4,
    )
    st.plotly_chart(fig_payment, use_container_width=True)

st.subheader("💰 Rata-Rata Nilai Transaksi per Metode Pembayaran ($)")
df_pay_val = (
    df_filtered.groupby("payment_type")["payment_value"].mean().reset_index()
)
fig_pay_val = px.bar(
    df_pay_val,
    x="payment_value",
    y="payment_type",
    orientation="h",
    labels={
        "payment_value": "Rata-Rata Pembayaran ($)",
        "payment_type": "Tipe Pembayaran",
    },
    color="payment_type",
)
st.plotly_chart(fig_pay_val, use_container_width=True)

# --- SITEMAP DATA / TABEL PREVIEW ---
with st.expander("📄 Lihat Sample Data Hasil Pipeline (Pandas Merge)"):
    st.dataframe(df_filtered.head(100))