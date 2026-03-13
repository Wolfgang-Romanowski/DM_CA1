import pandas as pd
import streamlit as st
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMS_DIR = os.path.join(BASE_DIR, "exams", "Discrete_Mathematics")

@st.cache_data
def load_questions():
    return pd.read_csv(os.path.join(BASE_DIR, "questions.csv"))

def show_question(row, show_detail=True):
  with st.container(border=True):
    st.subheader(f"{row['year']} {row['paper_type']} -- Q{row['question']} ({row['part']})")
    if show_detail:
        st.caption(
            f"**Topic:** {row['topic']} / {row['sub_topic']}  \n"
            f"**Task:** {row['task']}  \n"
            f"**Keywords:** {row['keywords']}  \n"
            f"**Difficulty:** {int(row['difficulty'])}/5 | **Marks:** {row['marks']}"
        )

    key = row['pdf'].replace("Discrete_Mathematics_", "").replace(".pdf", "")
    img = os.path.join(BASE_DIR, "page_images", key, f"page_{int(row['page'])}.png")
    if os.path.exists(img):
        with st.expander("View question"):
            st.image(img, width="stretch")

    c1, c2 = st.columns(2)
    exam_path = os.path.join(EXAMS_DIR, row['pdf'])
    if os.path.exists(exam_path):
        with open(exam_path, "rb") as f:
            c1.download_button("Download Exam", f.read(), file_name=row['pdf'],
                               mime="application/pdf", key=f"e_{row['id']}")
    if pd.notna(row.get('ms_pdf')) and str(row.get('ms_pdf', '')) != '':
        ms_path = os.path.join(EXAMS_DIR, row['ms_pdf'])
        if os.path.exists(ms_path):
            with open(ms_path, "rb") as f:
                c2.download_button("Download Marking Scheme", f.read(), file_name=row['ms_pdf'],
                                   mime="application/pdf", key=f"m_{row['id']}")
    st.divider()

def show_results(filtered, show_detail):
    st.write(f"**{len(filtered)} results**")
    for _, row in filtered.sort_values(['year','question','part'], ascending=[False,True,True]).iterrows():
        show_question(row, show_detail)