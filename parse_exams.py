import fitz
import os
import json
import time
import pandas as pd
from PIL import Image
import google.generativeai as genai

EXAMS_DIR = os.path.join("exams", "Discrete_Mathematics")
IMAGES_DIR = "page_images"
OUTPUT_CSV = "questions.csv"
DPI = 150

YEAR_MAP = {"202425":"2024/25", "202324":"2023/24", "202223":"2022/23",
            "202122":"2021/22", "2017":"2017", "2016":"2016",
            "2014":"2014", "2013":"2013"}

PROMPT = """Look at this exam paper page. Extract every question part visible.
For each part return a JSON object with:
- question: the question number (integer)
- part: the letter (a, b, c, d, etc.)
- topic: one of: logic, relations, functions, graphs, enumeration, sequences, collections
- sub_topic: short label like "truth tables", "properties", "n-bit strings", etc.
- task: one sentence describing what the student must do
- keywords: comma-separated relevant terms
- difficulty: 1-5 estimate
- marks: marks for this part (integer, 0 if unclear)

Return ONLY a JSON array. If the page is a cover page, formula sheet, or has no questions, return [].
"""


def render_all_pdfs():
    """Loop through every PDF in exams/ and save each page as a PNG."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    for filename in sorted(os.listdir(EXAMS_DIR)):
        if not filename.endswith(".pdf"):
            continue
        key = filename.replace("Discrete_Mathematics_", "").replace(".pdf", "")
        out_dir = os.path.join(IMAGES_DIR, key)
        os.makedirs(out_dir, exist_ok=True)

        doc = fitz.open(os.path.join(EXAMS_DIR, filename))
        for page_num in range(len(doc)):
            img_path = os.path.join(out_dir, f"page_{page_num + 1}.png")
            if not os.path.exists(img_path):  #skip if rendered already
                pix = doc[page_num].get_pixmap(dpi=DPI)
                pix.save(img_path)
        print(f"  {key}: {len(doc)} pages")
        doc.close()


def extract_questions_from_image(model, img_path):
    """Send a page image to Gemini, get back structured question data."""
    img = Image.open(img_path)
    response = model.generate_content([PROMPT, img])
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def build_questions_csv():
    """Extract questions from all exam pages using Gemini."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    rows = []
    for filename in sorted(os.listdir(EXAMS_DIR)):
        if not filename.endswith(".pdf") or "_MS" in filename:
            continue

        key = filename.replace("Discrete_Mathematics_", "").replace(".pdf", "")
        year = next((v for k, v in YEAR_MAP.items() if k in key), "Unknown")
        ptype = "Repeat" if "Repeat" in key else "Final"
        ms = filename.replace("_E.pdf", "_MS.pdf")
        if not os.path.exists(os.path.join(EXAMS_DIR, ms)):
            ms = ""

        img_dir = os.path.join(IMAGES_DIR, key)
        for page_file in sorted(os.listdir(img_dir)):
            page_num = int(page_file.replace("page_","").replace(".png",""))
            img_path = os.path.join(img_dir, page_file)

            try:
                parts = extract_questions_from_image(model, img_path)
            except Exception as e:
                print(f"    page {page_num}: error - {e}")
                continue

            for p in parts:
                rows.append({
                    "id": f"{year.replace('/','')}{ptype}_Q{p['question']}{p['part']}",
                    "year": year, "paper_type": ptype,
                    "question": p["question"], "part": p["part"],
                    "topic": p.get("topic",""), "sub_topic": p.get("sub_topic",""),
                    "task": p.get("task",""), "keywords": p.get("keywords",""),
                    "difficulty": p.get("difficulty",""), "marks": p.get("marks",""),
                    "page": page_num, "pdf": filename, "ms_pdf": ms,
                })

            if parts:
                print(f"    page {page_num}: {len(parts)} parts")

            time.sleep(4)  # free tier ratelimit

        print(f"  {key}: done")

    seen = set()
    unique = []
    for r in rows:
        if r['id'] not in seen:
            seen.add(r['id'])
            unique.append(r)

    pd.DataFrame(unique).to_csv(OUTPUT_CSV, index=False)
    print(f"\n{OUTPUT_CSV}: {len(unique)} questions")


if __name__ == "__main__":
    print("rendering exam PDF to image\n")
    render_all_pdfs()
    print("\npage images saved to:", IMAGES_DIR)
    print("\nextracting questions...\n")
    build_questions_csv()