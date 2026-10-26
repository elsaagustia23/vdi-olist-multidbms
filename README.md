# E-Commerce Customer Satisfaction & Order Analytics
*Multi-DBMS Data Pipeline & Web Visualization*

## 📌 Ringkasan Arsitektur Data Pipeline
Proyek ini mengintegrasikan dua sistem basis data berbeda di tingkat aplikasi (Python):
1. **Supabase (PostgreSQL - Relational):** Menyimpan data utama pesanan (`orders`) dan pelanggan (`customers`).
2. **MongoDB Atlas (NoSQL - Document Store):** Menyimpan log ulasan (`reviews`) dan metode pembayaran (`payments`).

Data dari kedua DBMS ditarik dan digabungkan menggunakan **Pandas (`pd.merge()`)** secara *real-time* sebelum disajikan pada antarmuka web interaktif berbasis Streamlit.

## 🔗 Sitasi & Referensi
- **Sumber Data Asli:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Referensi Kode/Arsitektur:** [Streamlit Documentation](https://docs.streamlit.io/) & [Supabase Python Docs](https://supabase.com/docs)