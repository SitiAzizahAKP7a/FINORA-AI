# FINORA AI
**Financial Analysis & Audit Intelligence**

Aplikasi Streamlit untuk analisis laporan keuangan, pemeriksaan data, penilaian risiko awal, analisis anggaran, arus kas, proyeksi sederhana, dan AI assistant berbantuan Google Gemini.

## Fitur
- Executive Financial Dashboard
- Custom Analysis (satu file untuk beberapa modul)
- Financial Statement Analysis
- Financial Ratio Analysis
- Automated Financial Audit
- Audit Risk Assessment
- Budget vs Actual Analysis
- Cash Flow Analysis
- Financial Forecasting
- FINORA AI Assistant (Gemini)
- Document & Evidence Checking (pencocokan tabel Excel/CSV; OCR belum diaktifkan)
- AI Audit Report Generator (PDF)
- Report Center & Export (CSV)

## 1. Jalankan di komputer
Pastikan Python 3.10 atau lebih baru sudah terpasang.

```bash
python -m venv .venv
```

Aktifkan virtual environment:

**Windows**
```bash
.venv\Scripts\activate
```

**Mac/Linux**
```bash
source .venv/bin/activate
```

Install kebutuhan:
```bash
pip install -r requirements.txt
```

Buat file `.env` dari `.env.example`, lalu isi:
```env
GEMINI_API_KEY=API_KEY_GEMINI_KAMU
```

Jalankan aplikasi:
```bash
streamlit run app.py
```

## 2. Upload ke GitHub
1. Buat repository baru di GitHub, misalnya `FINORA-AI`.
2. Upload seluruh isi folder project ini (bukan hanya app.py).
3. Jangan upload file `.env` atau API key ke GitHub.
4. Pastikan `app.py`, `requirements.txt`, folder `modules`, `services`, dan `assets` ikut ter-upload.

## 3. Deploy ke Streamlit Community Cloud
1. Buka https://share.streamlit.io/
2. Login menggunakan GitHub.
3. Pilih repository `FINORA-AI`.
4. Main file path: `app.py`.
5. Pada bagian App settings / Secrets, masukkan:

```toml
GEMINI_API_KEY = "API_KEY_GEMINI_KAMU"
```

6. Deploy aplikasi.

## Format file yang digunakan
- Excel/CSV umum: Financial Statement Analysis, Audit, Risk, Custom Analysis.
- Budget Analysis: wajib memiliki kolom `Category`, `Budget`, `Actual`.
- Cash Flow: siapkan kolom jenis arus (misalnya `Type` berisi Inflow/Outflow) dan nominal (misalnya `Amount`).
- Forecasting: pilih kolom periode dan satu kolom numerik.
- Ratio Analysis: masukkan saldo akun pada form rasio.

## Catatan penting
- Gemini hanya digunakan pada fitur yang memanggil AI. Analisis berbasis aturan tetap dapat berjalan tanpa API key.
- Hasil audit otomatis adalah indikasi awal, bukan opini audit, bukti kecurangan, atau pengganti pemeriksaan profesional.
- OCR invoice, kuitansi, dan bukti transfer belum diimplementasikan pada versi awal.
- Forecasting menggunakan tren linear sederhana dan tidak boleh dianggap sebagai jaminan hasil masa depan.
- Riwayat tersimpan di SQLite lokal. Pada hosting yang filesystem-nya sementara, data dapat hilang saat aplikasi di-redeploy atau instance di-reset. Untuk penggunaan produksi, gunakan database persisten.
