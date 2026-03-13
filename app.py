"""Run: streamlit run app.py"""
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import os
from helpers import load_questions, show_question, show_results, EXAMS_DIR

st.set_page_config(page_title="Discrete Maths Study Guide", layout="wide")
df = load_questions()

page = st.sidebar.selectbox("Navigate", [
    "Introduction",
    "Search by Topic",
    "Search by Keyword",
    "Search by Difficulty",
    "Search by Paper",
    "Exam Papers",
    "Statistics",
])
show_detail = st.sidebar.checkbox("Show question detail", value=True)


if page == "Introduction":
    st.title("Discrete Mathematics Exam Guide")
    st.caption(
        "Search and filter past exam questions by topic, keyword, difficulty, or paper.  \n"
        "Use the sidebar to navigate."
    )


elif page == "Search by Topic":
    st.title("Search by Topic")
    selected = st.multiselect("Select topic(s):", sorted(df['topic'].unique()))
    if selected:
        filtered = df[df['topic'].isin(selected)]
        sel_subs = st.multiselect("Narrow by sub-topic:", sorted(filtered['sub_topic'].unique()))
        if sel_subs:
            filtered = filtered[filtered['sub_topic'].isin(sel_subs)]
        show_results(filtered, show_detail)


elif page == "Search by Keyword":
    st.title("Search by Keyword")
    all_kw = sorted(set(k.strip() for kws in df['keywords'].dropna() for k in kws.split(",")))
    selected = st.multiselect("Select keywords:", all_kw)
    mode = st.radio("Match mode:", ["OR", "AND"], horizontal=True) if len(selected) > 1 else "OR"
    if selected:
        if mode == "AND":
            mask = df['keywords'].apply(lambda x: all(k in str(x) for k in selected))
        else:
            mask = df['keywords'].apply(lambda x: any(k in str(x) for k in selected))
        show_results(df[mask], show_detail)


elif page == "Search by Difficulty":
    st.title("Search by Difficulty")
    lo, hi = st.slider("Difficulty range:", 1, 5, (1, 3))
    show_results(df[(df['difficulty'] >= lo) & (df['difficulty'] <= hi)], show_detail)


elif page == "Search by Paper":
    st.title("Search by Paper")
    papers = df[['year','paper_type']].drop_duplicates().sort_values('year', ascending=False)
    choice = st.selectbox("Select paper:",
                          [f"{r['year']} {r['paper_type']}" for _, r in papers.iterrows()])
    year, ptype = choice.rsplit(" ", 1)
    filtered = df[(df['year'] == year) & (df['paper_type'] == ptype)].sort_values(['question','part'])
    st.caption(f"{len(filtered)} parts -- {int(filtered['marks'].sum())} marks")
    for _, row in filtered.iterrows():
        show_question(row, show_detail)


elif page == "Exam Papers":
    st.title("Exam Papers")
    for fname in sorted(os.listdir(EXAMS_DIR), reverse=True):
        if fname.endswith(".pdf"):
            label = fname.replace("Discrete_Mathematics_","").replace(".pdf","").replace("_"," ")
            with open(os.path.join(EXAMS_DIR, fname), "rb") as f:
                st.download_button(label, f.read(), file_name=fname,
                                   mime="application/pdf", key=fname, use_container_width=True)


elif page == "Statistics":
    st.title("Exam Paper Statistics")
    sns.set_style("darkgrid")

    fig, ax = plt.subplots(figsize=(10, 5))
    df.groupby(['year','topic']).size().unstack(fill_value=0).plot(
        kind='bar', stacked=True, ax=ax, colormap='Set2')
    ax.set_ylabel("# question parts"); ax.legend(bbox_to_anchor=(1.05, 1))
    plt.tight_layout(); st.pyplot(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    sns.countplot(data=df, x='difficulty', palette='RdYlGn_r', ax=ax2)
    ax2.set_xlabel("Difficulty"); plt.tight_layout(); st.pyplot(fig2)

    fig3, ax3 = plt.subplots(figsize=(10, 5))
    hm = df.groupby(['topic','year'])['marks'].sum().unstack(fill_value=0)
    sns.heatmap(hm, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax3, linewidths=0.5)
    plt.tight_layout(); st.pyplot(fig3)

    st.dataframe(
        df.groupby('topic').agg(
            questions=('id','count'), total_marks=('marks','sum'),
            avg_difficulty=('difficulty','mean')
        ).round(1).sort_values('total_marks', ascending=False),
        use_container_width=True
    )