import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
from rapidfuzz import fuzz
import pandas as pd

st.title("🗳️ Online Duplicate Voter Finder")

def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if not t:
                image = page.to_image(resolution=300).original
                t = pytesseract.image_to_string(image, lang="eng+hin")
            text += t + "\n"
    return text

def normalize(s):
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch.isspace()).strip()

def detect_duplicates(df, threshold=85):
    duplicates = []
    for i in range(len(df)):
        for j in range(i+1, len(df)):
            name1 = df.loc[i, "name"]
            name2 = df.loc[j, "name"]
            father1 = df.loc[i, "father"]
            father2 = df.loc[j, "father"]
            score = (fuzz.ratio(name1, name2) + fuzz.ratio(father1, father2)) / 2
            if score >= threshold:
                duplicates.append((i, j, score))
    return duplicates

uploaded = st.file_uploader("Upload multiple voter PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded:
    all_rows = []
    for file in uploaded:
        st.write(f"Processing: **{file.name}**")
        text = extract_text(file)
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for ln in lines:
            parts = ln.split()
            if len(parts) >= 2:
                name = normalize(" ".join(parts[:2]))
                father = normalize(" ".join(parts[2:4])) if len(parts) > 3 else ""
                all_rows.append({"name": name, "father": father, "raw": ln, "file": file.name})

    df = pd.DataFrame(all_rows)
    st.dataframe(df.head(50))

    duplicates = detect_duplicates(df)
    if duplicates:
        dup_list = []
        for i, j, score in duplicates:
            dup_list.append({
                "Record A": df.loc[i, "raw"],
                "Record B": df.loc[j, "raw"],
                "Match Score": score
            })
        dup_df = pd.DataFrame(dup_list)
        st.write("### 🔍 Potential Duplicates Found")
        st.dataframe(dup_df)
        st.download_button("Download Duplicate List CSV", dup_df.to_csv(index=False), "duplicates.csv")
    else:
        st.success("No duplicates found (Try lowering threshold).")
