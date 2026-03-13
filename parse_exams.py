import fitz
import os

EXAMS_DIR = os.path.join("exams", "Discrete_Mathematics")
IMAGES_DIR = "page_images"
DPI = 150


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
            if not os.path.exists(img_path):  #skip if rendered alreayd
                pix = doc[page_num].get_pixmap(dpi=DPI)
                pix.save(img_path)

        print(f"  {key}: {len(doc)} pages")
        doc.close()


if __name__ == "__main__":
    print("rendering exam PDF to image\n")
    render_all_pdfs()
    print("\npage images saved to:", IMAGES_DIR)