import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from rapidfuzz import fuzz, process

st.set_page_config(page_title="Duplicate Voter Finder", layout="wide")

# ------------------------ MULTI LANGUAGE SUPPORT -------------------------
LANG_OPTIONS = {
    "English": {
        "title": "🗳️ Online Duplicate Voter Finder",
        "upload_label": "Upload your voter list PDF files (multiple allowed)",
        "processing": "Processing PDFs... Please wait 🙏",
        "processed": "PDFs processed successfully! 🙌",
        "duplicate_title": "🔍 Duplicate Detection Running...",
        "no_duplicates": "🎉 No duplicates found!",
        "duplicates_found": "⚠️ {count} duplicate entries found!",
        "download": "⬇️ Download Duplicate Report (CSV)",
        "slider": "⚙️ Match Sensitivity (Similarity %)"
    },
    "हिंदी": {
        "title": "🗳️ ऑनलाइन डुप्लिकेट वोटर फाइंडर",
        "upload_label": "वोटर लिस्ट PDF अपलोड करें (एक से ज्यादा भी चलेगा)",
        "processing": "PDF प्रोसेस हो रहा है... कृपया प्रतीक्षा करें 🙏",
        "processed": "PDF सफलतापूर्वक प्रोसेस हो गया! 🙌",
        "duplicate_title": "🔍 डुप्लिकेट खोजा जा रहा है...",
        "no_duplicates": "🎉 कोई डुप्लिकेट नहीं मिला!",
        "duplicates_found": "⚠️ कुल {count} डुप्लिकेट एंट्री मिली!",
        "download": "⬇️ रिपोर्ट डाउनलोड करें (CSV)",
        "slider": "⚙️ मैच सेंसिटिविटी (प्रतिशत %)"
    },
    "বাংলা": {
        "title": "🗳️ অনলাইন ডুপ্লিকেট ভোটার সন্ধান",
        "upload_label": "আপনার ভোটার লিস্ট PDF আপলোড করুন (একাধিক ফাইল অনুমোদিত)",
        "processing": "PDF প্রক্রিয়া চলছে... অনুগ্রহ করে অপেক্ষা করুন 🙏",
        "processed": "PDF সফলভাবে প্রক্রিয়া সম্পন্ন হয়েছে! 🙌",
        "duplicate_title": "🔍 ডুপ্লিকেট খুঁজে দেখা হচ্ছে...",
        "no_duplicates": "🎉 কোনো ডুপ্লিকেট পাওয়া যায়নি!",
        "duplicates_found": "⚠️ মোট {count} টি ডুপ্লিকেট পাওয়া গেছে!",
        "download": "⬇️ ডুপ্লিকেট রিপোর্ট ডাউনলোড করুন (CSV)",
        "slider": "⚙️ ম্যাচ সেনসিটিভিটি (শতাংশ %)"
    }
}

# ------------------------ LANGUAGE SELECTOR -------------------------
lang = st.selectbox("🌐 Select Language / भाषा चुनें / ভাষা নির্বাচন করুন", list(LANG_OPTIONS.keys()))
TXT = LANG_OPTIONS[lang]

# ------------------------ UI -------------------------
st.title(TXT["title"])

threshold = st.slider(TXT["slider"], 60, 100, 85)

uploaded_files = st.file_uploader(
    TXT["upload_label"],
    type=["pdf"],
    accept_multiple_files=True
)

# ------------------------ PDF TEXT EXTRACTOR -------------------------
def extract_text_from_pdf(pdf_bytes):
    text_data = []
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in pdf:
        text_data.append(page.get_text())
    return "\n".join(text_data)

# ------------------------ CLEAN TEXT → NAMES -------------------------
def extract_names(text):
    lines = text.split("\n")
    clean = [line.strip() for line in lines if len(line.strip()) > 2]
    return clean

# ------------------------ MAIN PROCESS -------------------------
if uploaded_files:
    st.info(TXT["processing"])
    progress = st.progress(0)

    all_names = []
    total_files = len(uploaded_files)

    for i, pdf in enumerate(uploaded_files):
        progress.progress(int(((i + 1) / total_files) * 100))
        pdf_text = extract_text_from_pdf(pdf.read())
        names = extract_names(pdf_text)
        all_names.extend(names)

    st.success(TXT["processed"])

    st.subheader(TXT["duplicate_title"])
    df = pd.DataFrame({"Name": all_names})

    # Fuzzy duplicate finder
    duplicates = []
    used = set()

    for i, name in enumerate(df["Name"]):
        if name in used:
            continue

        matches = process.extract(name, df["Name"], scorer=fuzz.WRatio, limit=10)
        for match_name, score, idx in matches:
            if score >= threshold and idx != i:
                duplicates.append([name, match_name, score])
                used.add(match_name)

    if not duplicates:
        st.success(TXT["no_duplicates"])
    else:
        st.error(TXT["duplicates_found"].format(count=len(duplicates)))

        result_df = pd.DataFrame(duplicates, columns=["Name", "Matched With", "Similarity Score"])
        st.dataframe(result_df, use_container_width=True)

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=TXT["download"],
            data=csv,
            file_name="duplicate_voters.csv",
            mime="text/csv"
        )
