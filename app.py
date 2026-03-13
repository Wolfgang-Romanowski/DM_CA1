"""Run: streamlit run app.py"""
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import os
from helpers import load_questions, show_question, show_results, EXAMS_DIR
import fitz
import io

st.set_page_config(page_title="Discrete Maths Study Guide", layout="wide")
df = load_questions()

if "selected_questions" not in st.session_state:
    st.session_state.selected_questions = set()

page = st.sidebar.selectbox("Navigate", [
    "Introduction",
    "Search by Topic",
    "Search by Keyword",
    "Search by Difficulty",
    "Search by Paper",
    "Exam Papers",
    "Statistics",
    "Classify a Question",
    "Practice Set",
])
show_detail = st.sidebar.checkbox("Show question detail", value=True)
ps_count = len(st.session_state.selected_questions)
if ps_count > 0:
    st.sidebar.caption(f"Practice set: {ps_count} questions selected")

if page == "Introduction":
    st.title("Discrete Mathematics Exam Guide")
    st.write(
        "Search and filter past exam questions by topic, keyword, difficulty, or paper. "
        "Use the sidebar to navigate."
    )
 
    st.divider()
 
    col1, col2, col3 = st.columns(3)
    col1.metric("Questions", len(df))
    col2.metric("Papers", df[['year','paper_type']].drop_duplicates().shape[0])
    col3.metric("Topics", df['topic'].nunique())
 
    st.divider()
 
    st.subheader("Topics covered")
    for topic in sorted(df['topic'].unique()):
        subs = sorted(df[df['topic']==topic]['sub_topic'].unique())
        count = len(df[df['topic']==topic])
        st.caption(f"**{topic}** ({count} questions) -- {', '.join(subs)}")
 
    st.divider()
 
    st.subheader("Papers available")
    papers = df.groupby(['year','paper_type']).agg(
        parts=('id','count'), marks=('marks','sum')
    ).reset_index().sort_values('year', ascending=False)
    st.dataframe(papers, width="stretch", hide_index=True)


elif page == "Search by Topic":
    st.title("Search by Topic")
    with st.expander("How does this work?"):
        st.write("Select one or more topics to see all matching questions. "
                 "Optionally narrow down by sub-topic.")
    selected = st.multiselect("Select topic(s):", sorted(df['topic'].unique()))
    if selected:
        filtered = df[df['topic'].isin(selected)]
        sel_subs = st.multiselect("Narrow by sub-topic:", sorted(filtered['sub_topic'].unique()))
        if sel_subs:
            filtered = filtered[filtered['sub_topic'].isin(sel_subs)]
        show_results(filtered, show_detail)
 
 
elif page == "Search by Keyword":
    st.title("Search by Keyword")
    with st.expander("How does this work?"):
        st.write("Select keywords that appear in question descriptions. "
                 "OR finds questions with any keyword. AND requires all keywords.")
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
    with st.expander("How does this work?"):
        st.write("Difficulty is rated 1-5. "
                 "1 = straightforward recall. 5 = very challenging, requires insight.")
    lo, hi = st.slider("Difficulty range:", 1, 5, (1, 3))
    show_results(df[(df['difficulty'] >= lo) & (df['difficulty'] <= hi)], show_detail)
 
 
elif page == "Search by Paper":
    st.title("Search by Paper")
    papers = df[['year','paper_type']].drop_duplicates().sort_values('year', ascending=False)
    choice = st.selectbox("Select paper:",
                          [f"{r['year']} {r['paper_type']}" for _, r in papers.iterrows()])
    year, ptype = choice.rsplit(" ", 1)
    filtered = df[(df['year'] == year) & (df['paper_type'] == ptype)].sort_values(['question','part'])
 
    c1, c2, c3 = st.columns(3)
    c1.metric("Parts", len(filtered))
    c2.metric("Total marks", int(filtered['marks'].sum()))
    c3.metric("Avg difficulty", f"{filtered['difficulty'].mean():.1f}")
 
    st.divider()
    for _, row in filtered.iterrows():
        show_question(row, show_detail)
 
 
elif page == "Exam Papers":
    st.title("Exam Papers")
    for fname in sorted(os.listdir(EXAMS_DIR), reverse=True):
        if fname.endswith(".pdf"):
            label = fname.replace("Discrete_Mathematics_","").replace(".pdf","").replace("_"," ")
            with open(os.path.join(EXAMS_DIR, fname), "rb") as f:
                st.download_button(label, f.read(), file_name=fname,
                                   mime="application/pdf", key=fname)


elif page == "Statistics":
    st.title("Exam Paper Statistics")
    sns.set_style("darkgrid")
 
    tab1, tab2, tab3, tab4 = st.tabs(["Topics per year", "Difficulty", "Marks heatmap", "Summary"])
 
    with tab1:
        fig, ax = plt.subplots(figsize=(10, 5))
        df.groupby(['year','topic']).size().unstack(fill_value=0).plot(
            kind='bar', stacked=True, ax=ax, colormap='Set2')
        ax.set_ylabel("# question parts"); ax.legend(bbox_to_anchor=(1.05, 1))
        plt.tight_layout(); st.pyplot(fig)
 
    with tab2:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.countplot(data=df, x='difficulty', palette='RdYlGn_r', ax=ax2)
        ax2.set_xlabel("Difficulty"); plt.tight_layout(); st.pyplot(fig2)
 
    with tab3:
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        hm = df.groupby(['topic','year'])['marks'].sum().unstack(fill_value=0)
        sns.heatmap(hm, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax3, linewidths=0.5)
        plt.tight_layout(); st.pyplot(fig3)
 
    with tab4:
        st.dataframe(
            df.groupby('topic').agg(
                questions=('id','count'), total_marks=('marks','sum'),
                avg_difficulty=('difficulty','mean')
            ).round(1).sort_values('total_marks', ascending=False),
            width="stretch"
        )

elif page == "Classify a Question":
    st.title("Classify a Question")
    st.caption("Type a question description and the classifier predicts its topic. "
               "Uses TF-IDF + Naive Bayes trained on the existing question database.")
 
    from classifier import load_and_train, classify
    topic_model, sub_model, _ = load_and_train()
 
    text = st.text_input("Question description:",
                         placeholder="e.g. construct a truth table for the proposition")
    if text:
        topic, sub = classify(text, topic_model, sub_model)
        c1, c2 = st.columns(2)
        c1.metric("Topic", topic)
        c2.metric("Sub-topic", sub)
 
        st.divider()
        st.caption("Similar questions in the database:")
        matches = df[df['topic'] == topic].head(5)
        for _, row in matches.iterrows():
            show_question(row, show_detail=True)

elif page == "Practice Set":
    st.title("Practice Set")
    st.caption("Select questions to build a custom practice paper and download as pdf")
    #filter to narrow down before selecting
    col1, col2, col3 = st.columns(3)
    f_topic = col1.multiselect("Filter by topic:", sorted(df['topic'].unique()))
    f_year = col2.multiselect("Filter by year:", sorted(df['year'].unique(), reverse=True))
    f_diff = col3.slider("Difficulty:", 1, 5, (1, 5), key="ps_diff")
 
    pool = df.copy()
    if f_topic:
        pool = pool[pool['topic'].isin(f_topic)]
    if f_year:
        pool = pool[pool['year'].isin(f_year)]
    pool = pool[(pool['difficulty'] >= f_diff[0]) & (pool['difficulty'] <= f_diff[1])]
    pool = pool.sort_values(['year','question','part'], ascending=[False,True,True])
 
    total_selected = len(st.session_state.selected_questions)
    st.write(f"**{len(pool)} questions shown** ({total_selected} selected overall)")
 
    #checkboxes
    for _, row in pool.iterrows():
        qid = row['id']
        was_selected = qid in st.session_state.selected_questions
        label = f"Q{row['question']}({row['part']}) -- {row['year']} {row['paper_type']} -- {row['topic']} ({row['marks']} marks)"
        checked = st.checkbox(label, value=was_selected, key=f"ps_{qid}")
 
        if checked and not was_selected:
            st.session_state.selected_questions.add(qid)
        elif not checked and was_selected:
            st.session_state.selected_questions.discard(qid)
 
    selected_ids = st.session_state.selected_questions
    if selected_ids:
        selected_rows = df[df['id'].isin(selected_ids)]
        total_marks = int(selected_rows['marks'].sum())

        st.divider()
        st.write(f"**Selected: {len(selected_ids)} questions, {total_marks} marks**")

        if st.button("Clear all selections"):
            st.session_state.selected_questions = set()
            st.rerun()

        output_pdf = fitz.open()
        added_pages = set()

        for _, row in selected_rows.sort_values(['year','question','part']).iterrows():
            pdf_path = os.path.join(EXAMS_DIR, row['pdf'])
            page_key = (row['pdf'], int(row['page']))
            if page_key in added_pages or not os.path.exists(pdf_path):
                continue
            added_pages.add(page_key)

            src = fitz.open(pdf_path)
            output_pdf.insert_pdf(src, from_page=int(row['page'])-1, to_page=int(row['page'])-1)
            src.close()

        if added_pages:
            buf = io.BytesIO()
            output_pdf.save(buf)
            output_pdf.close()

            st.download_button(
                f"Download Practice Set ({len(added_pages)} pages, {total_marks} marks)",
                buf.getvalue(),
                file_name="practice_set.pdf",
                mime="application/pdf",
            )
        else:
            output_pdf.close()