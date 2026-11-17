import os
from io import BytesIO
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =========================================================
# FINORA AI - SINGLE FILE VERSION
# Hanya membutuhkan app.py dan requirements.txt
# =========================================================

st.set_page_config(
    page_title="FINORA AI",
    page_icon="💗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------- STYLE -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #FFF9F5; }
h1, h2, h3 { color: #442A36; }
h1 { font-family: 'Playfair Display', serif; }
[data-testid="stSidebar"] { background: #FFF0F3; border-right: 1px solid #F5D9E1; }
[data-testid="stMetric"] { background: white; border: 1px solid #F4DCE3; padding: 14px; border-radius: 14px; }
.stButton > button, .stDownloadButton > button { border-radius: 10px; border: 1px solid #FF5C8B; }
.stButton > button[kind="primary"] { background: #FF5C8B; color: white; }
.finora-hero { padding: 1.3rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#FF5C8B,#F7A6B9); color: white; margin-bottom: 1rem; }
.finora-hero h1 { color: white; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ------------------------- SESSION -------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "active_df" not in st.session_state:
    st.session_state.active_df = None
if "active_filename" not in st.session_state:
    st.session_state.active_filename = ""

def save_history(module, filename="", summary="", risk="Belum dinilai"):
    st.session_state.history.insert(0, {
        "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Modul": module,
        "Nama File": filename,
        "Ringkasan": summary,
        "Risiko": risk
    })

def read_file(uploaded, sheet=None):
    uploaded.seek(0)
    if uploaded.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded)
    return pd.read_excel(uploaded, sheet_name=sheet or 0)

def uploader(key):
    up = st.file_uploader("Unggah file Excel (.xlsx) atau CSV", type=["xlsx", "xlsm", "csv"], key=key)
    if up is None:
        return None, None
    try:
        if up.name.lower().endswith((".xlsx", ".xlsm")):
            up.seek(0)
            xls = pd.ExcelFile(up)
            if len(xls.sheet_names) > 1:
                sheet = st.selectbox("Pilih sheet", xls.sheet_names, key=f"{key}_sheet")
            else:
                sheet = xls.sheet_names[0]
            up.seek(0)
            return pd.read_excel(up, sheet_name=sheet), up.name
        return read_file(up), up.name
    except Exception as e:
        st.error(f"File tidak dapat dibaca: {e}")
        return None, up.name

def ai_answer(prompt):
    api_key = ""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass
    api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Gemini API Key belum diatur. Tambahkan GEMINI_API_KEY pada Streamlit Secrets.")
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text or "Tidak ada jawaban dari Gemini."

def ai_panel(df, module, filename):
    st.markdown("#### ✨ Analisis dengan FINORA AI")
    question = st.text_area("Pertanyaan atau instruksi", key=f"question_{module}",
                            placeholder="Contoh: Jelaskan kondisi data dan hal yang perlu diperhatikan.")
    if st.button("Analisis dengan Gemini", type="primary", key=f"ask_{module}"):
        with st.spinner("FINORA AI sedang menganalisis data..."):
            try:
                prompt = f"""Anda adalah FINORA AI, asisten analisis keuangan dan audit.
Modul: {module}
Nama file: {filename}
Data (maksimal 120 baris):
{df.head(120).to_string(index=False)}
Pertanyaan: {question or 'Berikan ringkasan, temuan yang terlihat, keterbatasan data, dan rekomendasi.'}
Jawab dalam Bahasa Indonesia. Bedakan fakta dari dugaan. Jangan mengarang penyebab atau menyimpulkan kecurangan tanpa bukti."""
                answer = ai_answer(prompt)
                st.markdown(answer)
                save_history(module, filename, "Analisis AI dibuat")
            except Exception as e:
                st.error(str(e))

def basic_audit(df):
    findings = []
    duplicates = int(df.duplicated().sum())
    if duplicates:
        findings.append({"Temuan":"Baris duplikat","Jumlah":duplicates,"Risiko":"Sedang",
                         "Rekomendasi":"Periksa apakah transaksi tercatat lebih dari satu kali."})
    missing = int(df.isna().sum().sum())
    if missing:
        findings.append({"Temuan":"Nilai kosong","Jumlah":missing,"Risiko":"Sedang",
                         "Rekomendasi":"Lengkapi atau klarifikasi kolom yang masih kosong."})
    for col in df.select_dtypes(include=np.number).columns:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) >= 5:
            q1, q3 = vals.quantile(.25), vals.quantile(.75)
            iqr = q3-q1
            if iqr > 0:
                count = int(((vals < q1-1.5*iqr) | (vals > q3+1.5*iqr)).sum())
                if count:
                    findings.append({"Temuan":f"Nilai ekstrem pada {col}","Jumlah":count,"Risiko":"Tinggi",
                                     "Rekomendasi":"Telusuri dokumen sumber; nilai ekstrem bukan otomatis kesalahan."})
    debit = next((c for c in df.columns if str(c).strip().lower() in ["debit","debet"]), None)
    kredit = next((c for c in df.columns if str(c).strip().lower() in ["kredit","credit"]), None)
    if debit and kredit:
        d = pd.to_numeric(df[debit], errors="coerce").fillna(0).sum()
        k = pd.to_numeric(df[kredit], errors="coerce").fillna(0).sum()
        if not np.isclose(d,k):
            findings.append({"Temuan":"Total debit dan kredit tidak seimbang","Jumlah":1,"Risiko":"Tinggi",
                             "Rekomendasi":f"Telusuri selisih debit-kredit sebesar {d-k:,.2f}."})
    return findings

def risk_level(findings):
    if any(x["Risiko"]=="Tinggi" for x in findings): return "Tinggi"
    if any(x["Risiko"]=="Sedang" for x in findings): return "Sedang"
    return "Rendah"

# ------------------------- NAVIGATION -------------------------
pages = {
    "Overview": ["Executive Financial Dashboard", "Custom Analysis"],
    "Financial Analysis": ["Financial Statement Analysis", "Financial Ratio Analysis",
                           "Budget vs Actual Analysis", "Cash Flow Analysis", "Financial Forecasting"],
    "Audit & Risk": ["Automated Financial Audit", "Audit Risk Assessment",
                     "Document & Evidence Checking", "AI Audit Report Generator"],
    "AI & Reports": ["FINORA AI Assistant", "Report Center & Export"]
}
st.sidebar.markdown("""
<div style="padding:12px 4px 18px 4px;">
<div style="font-size:30px;font-weight:800;color:#FF5C8B;letter-spacing:1px;">FINORA AI</div>
<div style="font-size:11px;color:#80616D;">FINANCIAL ANALYSIS & AUDIT INTELLIGENCE</div>
</div>
""", unsafe_allow_html=True)
flat = [(group, page) for group, items in pages.items() for page in items]
selected = st.sidebar.radio("NAVIGATION", [f"{g} / {p}" for g,p in flat])
page = selected.split(" / ", 1)[1]
st.sidebar.divider()
st.sidebar.caption("Signature Pink · #FF5C8B")
st.sidebar.caption("Versi single-file: app.py + requirements.txt")

st.markdown("""
<div class="finora-hero">
<h1>FINORA AI</h1>
<div>Financial Analysis & Audit Intelligence</div>
<div style="font-size:13px;margin-top:6px;">Smart Financial Report Analysis, Automated Audit & AI-Powered Insights</div>
</div>
""", unsafe_allow_html=True)

# ------------------------- PAGE: DASHBOARD -------------------------
if page == "Executive Financial Dashboard":
    st.title("Executive Financial Dashboard")
    hist = st.session_state.history
    c1,c2,c3 = st.columns(3)
    c1.metric("Aktivitas tersimpan", len(hist))
    c2.metric("Risiko tinggi", sum(1 for x in hist if x["Risiko"]=="Tinggi"))
    c3.metric("Modul digunakan", len(set(x["Modul"] for x in hist)))
    if hist:
        hdf = pd.DataFrame(hist)
        st.subheader("Aktivitas terbaru")
        st.dataframe(hdf, use_container_width=True, hide_index=True)
        counts = hdf["Modul"].value_counts().rename_axis("Modul").reset_index(name="Jumlah")
        st.plotly_chart(px.bar(counts, x="Modul", y="Jumlah", color_discrete_sequence=["#FF5C8B"]), use_container_width=True)
    else:
        st.info("Belum ada aktivitas. Jalankan modul analisis untuk mengisi dashboard.")

# ------------------------- PAGE: CUSTOM ANALYSIS -------------------------
elif page == "Custom Analysis":
    st.title("Custom Analysis")
    st.write("Unggah satu file dan pilih beberapa jenis analisis.")
    df, name = uploader("custom_upload")
    if df is not None:
        st.dataframe(df.head(30), use_container_width=True)
        options = ["Financial Statement Analysis","Automated Financial Audit","Audit Risk Assessment",
                   "Budget vs Actual Analysis","Cash Flow Analysis"]
        chosen = st.multiselect("Pilih modul", options, default=["Financial Statement Analysis","Automated Financial Audit"])
        if st.button("Jalankan analisis terpilih", type="primary", disabled=not chosen):
            for item in chosen:
                st.markdown(f"### {item}")
                if item in ["Automated Financial Audit","Audit Risk Assessment"]:
                    findings = basic_audit(df)
                    st.dataframe(pd.DataFrame(findings) if findings else pd.DataFrame([{"Status":"Tidak ada indikasi dari pengujian dasar"}]), use_container_width=True)
                    st.caption(f"Tingkat risiko indikatif: {risk_level(findings)}")
                    save_history(item, name, f"{len(findings)} indikasi", risk_level(findings))
                elif item == "Budget vs Actual Analysis":
                    if all(c in df.columns for c in ["Category","Budget","Actual"]):
                        tmp=df.copy()
                        tmp["Budget"]=pd.to_numeric(tmp["Budget"],errors="coerce")
                        tmp["Actual"]=pd.to_numeric(tmp["Actual"],errors="coerce")
                        tmp["Variance"]=tmp["Actual"]-tmp["Budget"]
                        st.dataframe(tmp,use_container_width=True)
                    else: st.warning("Dilewati: kolom Category, Budget, Actual tidak lengkap.")
                else:
                    st.write(f"Data memiliki {len(df)} baris dan {len(df.columns)} kolom.")
                if item == "Financial Statement Analysis":
                    st.dataframe(df.describe(include="all").T, use_container_width=True)
        ai_panel(df, "Custom Analysis", name)

# ------------------------- PAGE: FINANCIAL STATEMENT -------------------------
elif page == "Financial Statement Analysis":
    st.title(page)
    st.write("Tinjauan data laporan keuangan dan ringkasan statistik.")
    df,name=uploader("statement_upload")
    if df is not None:
        st.caption(f"{name} · {len(df)} baris · {len(df.columns)} kolom")
        st.dataframe(df,use_container_width=True)
        numeric=df.select_dtypes("number")
        if not numeric.empty: st.dataframe(numeric.describe().T,use_container_width=True)
        ai_panel(df,page,name)

# ------------------------- PAGE: RATIO -------------------------
elif page == "Financial Ratio Analysis":
    st.title(page)
    st.write("Masukkan saldo akun untuk menghitung rasio keuangan.")
    a,b=st.columns(2)
    current_assets=a.number_input("Aset lancar",min_value=0.0)
    inventory=a.number_input("Persediaan",min_value=0.0)
    total_assets=a.number_input("Total aset",min_value=0.0)
    revenue=a.number_input("Pendapatan bersih",min_value=0.0)
    current_liabilities=b.number_input("Liabilitas lancar",min_value=0.0)
    total_debt=b.number_input("Total liabilitas",min_value=0.0)
    equity=b.number_input("Total ekuitas",min_value=0.0)
    gross_profit=b.number_input("Laba kotor")
    net_profit=a.number_input("Laba bersih")
    ratios=[
        ("Current Ratio", f"{current_assets/current_liabilities:.2f} kali" if current_liabilities else "Tidak dapat dihitung"),
        ("Quick Ratio", f"{(current_assets-inventory)/current_liabilities:.2f} kali" if current_liabilities else "Tidak dapat dihitung"),
        ("Debt to Equity Ratio", f"{total_debt/equity:.2f} kali" if equity else "Tidak dapat dihitung"),
        ("Debt to Asset Ratio", f"{total_debt/total_assets*100:.2f}%" if total_assets else "Tidak dapat dihitung"),
        ("Gross Profit Margin", f"{gross_profit/revenue*100:.2f}%" if revenue else "Tidak dapat dihitung"),
        ("Net Profit Margin", f"{net_profit/revenue*100:.2f}%" if revenue else "Tidak dapat dihitung"),
        ("Return on Assets", f"{net_profit/total_assets*100:.2f}%" if total_assets else "Tidak dapat dihitung"),
        ("Return on Equity", f"{net_profit/equity*100:.2f}%" if equity else "Tidak dapat dihitung")
    ]
    rdf=pd.DataFrame(ratios,columns=["Rasio","Hasil"])
    st.dataframe(rdf,use_container_width=True,hide_index=True)
    st.caption("Interpretasi rasio perlu mempertimbangkan industri, periode, kebijakan akuntansi, dan kualitas data.")
    if st.button("Interpretasikan dengan Gemini"):
        try: st.markdown(ai_answer("Interpretasikan rasio berikut secara hati-hati. Jangan mengarang benchmark industri.\n"+rdf.to_string(index=False)))
        except Exception as e: st.error(str(e))

# ------------------------- PAGE: AUTOMATED AUDIT -------------------------
elif page in ["Automated Financial Audit","Audit Risk Assessment"]:
    st.title(page)
    st.write("Pengujian awal atas data untuk mengidentifikasi hal yang perlu ditelusuri.")
    df,name=uploader("audit_upload")
    if df is not None:
        findings=basic_audit(df)
        if findings: st.dataframe(pd.DataFrame(findings),use_container_width=True,hide_index=True)
        else: st.success("Tidak ditemukan indikasi dari pengujian dasar yang tersedia.")
        level=risk_level(findings)
        st.metric("Tingkat risiko indikatif",level)
        st.warning("Hasil ini merupakan indikasi awal, bukan kesimpulan audit atau bukti kecurangan. Verifikasi dengan dokumen sumber.")
        if st.button("Simpan hasil pemeriksaan"):
            save_history(page,name,f"{len(findings)} indikasi",level)
            st.success("Tersimpan pada riwayat sesi ini.")

# ------------------------- PAGE: BUDGET -------------------------
elif page == "Budget vs Actual Analysis":
    st.title(page)
    st.write("Gunakan kolom Category, Budget, dan Actual.")
    df,name=uploader("budget_upload")
    if df is not None:
        required=["Category","Budget","Actual"]
        if not all(c in df.columns for c in required):
            st.error("Kolom wajib: Category, Budget, Actual.")
        else:
            df["Budget"]=pd.to_numeric(df["Budget"],errors="coerce")
            df["Actual"]=pd.to_numeric(df["Actual"],errors="coerce")
            if df[["Budget","Actual"]].isna().any().any(): st.error("Budget dan Actual harus berupa angka.")
            else:
                df["Variance"]=df["Actual"]-df["Budget"]
                df["Variance %"]=df["Variance"].div(df["Budget"].replace(0,np.nan))*100
                c1,c2,c3=st.columns(3)
                c1.metric("Total Budget",f"{df.Budget.sum():,.2f}")
                c2.metric("Total Actual",f"{df.Actual.sum():,.2f}")
                c3.metric("Total Variance",f"{df.Variance.sum():,.2f}")
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.plotly_chart(px.bar(df,x="Category",y="Variance",color="Variance",color_continuous_scale=["#B4234D","#F4D6A0","#68A88A"]),use_container_width=True)
                st.plotly_chart(px.bar(df,x="Category",y=["Budget","Actual"],barmode="group"),use_container_width=True)
                if st.button("Simpan analisis anggaran"): save_history(page,name,f"Selisih {df.Variance.sum():,.2f}")

# ------------------------- PAGE: CASH FLOW -------------------------
elif page == "Cash Flow Analysis":
    st.title(page)
    st.write("Analisis arus kas masuk, arus kas keluar, dan arus kas bersih.")
    df,name=uploader("cash_upload")
    if df is not None:
        st.dataframe(df,use_container_width=True)
        amount=next((c for c in df.columns if str(c).lower() in ["amount","nominal","jumlah","nilai"]),None)
        typ=next((c for c in df.columns if str(c).lower() in ["type","jenis","arus","kategori"]),None)
        if not amount or not typ:
            st.info("Sediakan kolom nominal/jumlah dan jenis/type berisi Inflow atau Outflow.")
        else:
            df[amount]=pd.to_numeric(df[amount],errors="coerce")
            labels=df[typ].astype(str).str.lower()
            inflow=df.loc[labels.str.contains("inflow|masuk|penerimaan"),amount].sum()
            outflow=df.loc[labels.str.contains("outflow|keluar|pengeluaran"),amount].sum()
            x,y,z=st.columns(3)
            x.metric("Cash Inflow",f"{inflow:,.2f}")
            y.metric("Cash Outflow",f"{outflow:,.2f}")
            z.metric("Net Cash Flow",f"{inflow-outflow:,.2f}")
            ai_panel(df,page,name)

# ------------------------- PAGE: FORECAST -------------------------
elif page == "Financial Forecasting":
    st.title(page)
    st.write("Proyeksi tren linear sederhana berdasarkan data historis.")
    df,name=uploader("forecast_upload")
    if df is not None:
        numeric=list(df.select_dtypes("number").columns)
        if not numeric: st.warning("Tidak ada kolom numerik untuk diproyeksikan.")
        else:
            metric=st.selectbox("Pilih nilai",numeric)
            periods=st.slider("Jumlah periode proyeksi",1,12,3)
            if st.button("Buat proyeksi",type="primary"):
                series=pd.to_numeric(df[metric],errors="coerce").dropna().reset_index(drop=True)
                if len(series)<2: st.error("Minimal diperlukan dua periode data.")
                else:
                    slope,intercept=np.polyfit(np.arange(len(series)),series,1)
                    future=np.arange(len(series),len(series)+periods)
                    fut=pd.DataFrame({"Periode":np.arange(len(series)+1,len(series)+periods+1),"Nilai Proyeksi":slope*future+intercept})
                    hist=pd.DataFrame({"Periode":np.arange(1,len(series)+1),"Nilai":series})
                    st.plotly_chart(px.line(hist,x="Periode",y="Nilai",markers=True),use_container_width=True)
                    st.dataframe(fut,use_container_width=True,hide_index=True)
                    st.caption("Proyeksi ini bukan jaminan kondisi masa depan; pertimbangkan faktor eksternal dan validasi model.")

# ------------------------- PAGE: EVIDENCE -------------------------
elif page == "Document & Evidence Checking":
    st.title(page)
    st.write("Pencocokan daftar transaksi dengan daftar bukti berbasis tabel Excel/CSV.")
    st.info("OCR untuk membaca gambar, invoice, kuitansi, atau PDF belum tersedia pada versi ini.")
    tx,txname=uploader("evidence_transactions")
    ev,evname=uploader("evidence_register")
    if tx is not None and ev is not None:
        common=[c for c in tx.columns if c in ev.columns]
        if common:
            key=st.selectbox("Pilih kolom referensi yang sama",common)
            right=set(ev[key].astype(str).str.strip())
            result=tx.copy()
            result["Status Pencocokan"]=tx[key].astype(str).str.strip().apply(lambda v:"Cocok" if v in right else "Belum ditemukan")
            st.dataframe(result,use_container_width=True,hide_index=True)
            st.metric("Belum ditemukan",int((result["Status Pencocokan"]=="Belum ditemukan").sum()))
        else: st.warning("Tidak ada nama kolom yang sama pada kedua file.")

# ------------------------- PAGE: AI ASSISTANT -------------------------
elif page == "FINORA AI Assistant":
    st.title(page)
    st.write("Tanyakan hal terkait keuangan dan audit kepada FINORA AI.")
    df,name=uploader("assistant_upload")
    if df is not None:
        st.caption(f"Data aktif: {name}")
        st.dataframe(df.head(25),use_container_width=True)
    question=st.text_area("Pertanyaan",placeholder="Contoh: Apa temuan penting dari data ini?")
    if st.button("Tanyakan kepada FINORA AI",type="primary") and question:
        with st.spinner("Gemini sedang menyiapkan jawaban..."):
            try:
                context=df.head(120).to_string(index=False) if df is not None else "Tidak ada file yang diunggah."
                st.markdown(ai_answer(f"Anda FINORA AI, asisten analisis keuangan. Jawab dalam Bahasa Indonesia. Data:\n{context}\nPertanyaan: {question}\nJangan mengarang informasi yang tidak tersedia."))
            except Exception as e: st.error(str(e))

# ------------------------- PAGE: PDF REPORT -------------------------
elif page == "AI Audit Report Generator":
    st.title(page)
    st.write("Membuat draf laporan pemeriksaan awal dalam format PDF.")
    df,name=uploader("report_upload")
    if df is not None:
        findings=basic_audit(df)
        st.dataframe(pd.DataFrame(findings) if findings else pd.DataFrame([{"Status":"Tidak ada indikasi pengujian dasar"}]),use_container_width=True)
        scope=st.text_input("Tujuan/ruang lingkup pemeriksaan","Pemeriksaan awal atas data yang diunggah")
        period=st.text_input("Periode data","Belum ditentukan")
        if st.button("Buat laporan PDF",type="primary"):
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                buffer=BytesIO()
                doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=1.7*cm,leftMargin=1.7*cm,topMargin=1.7*cm,bottomMargin=1.7*cm)
                styles=getSampleStyleSheet()
                styles.add(ParagraphStyle(name="FinoraTitle",parent=styles["Title"],textColor=colors.HexColor("#B83F68")))
                story=[Paragraph("FINORA AI - Draf Laporan Pemeriksaan",styles["FinoraTitle"]),Spacer(1,12)]
                paragraphs=[f"Nama file: {name}",f"Ruang lingkup: {scope}",f"Periode: {period}",f"Jumlah baris: {len(df)}",f"Tingkat risiko indikatif: {risk_level(findings)}","Catatan: laporan ini merupakan draf pemeriksaan awal dan harus diverifikasi sebelum digunakan secara resmi."]
                for p in paragraphs: story.extend([Paragraph(p,styles["BodyText"]),Spacer(1,7)])
                if findings:
                    rows=[["Temuan","Jumlah","Risiko","Rekomendasi"]]+[[x["Temuan"],str(x["Jumlah"]),x["Risiko"],x["Rekomendasi"]] for x in findings]
                    table=Table(rows,repeatRows=1)
                    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#FF5C8B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#E8C8D2")),("FONTSIZE",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP")]))
                    story.append(table)
                doc.build(story)
                st.download_button("Unduh PDF",buffer.getvalue(),file_name="FINORA_AI_Laporan.pdf",mime="application/pdf")
            except Exception as e: st.error(f"Gagal membuat PDF: {e}")

# ------------------------- PAGE: REPORT CENTER -------------------------
elif page == "Report Center & Export":
    st.title(page)
    st.write("Riwayat aktivitas pada sesi aplikasi ini.")
    if st.session_state.history:
        hdf=pd.DataFrame(st.session_state.history)
        st.dataframe(hdf,use_container_width=True,hide_index=True)
        st.download_button("Unduh riwayat CSV",hdf.to_csv(index=False).encode("utf-8-sig"),"FINORA_AI_Riwayat.csv","text/csv")
    else: st.info("Belum ada aktivitas yang tersimpan. Riwayat versi ini tersimpan selama sesi aplikasi berjalan.")

st.sidebar.divider()
st.sidebar.caption("FINORA AI · Financial Analysis & Audit Intelligence")
