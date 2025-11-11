# backend/IA/save_pdf.py
from fpdf import FPDF
from docx import Document

def save_as_pdf(text, filename="transcription.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    #pdf.cell(0, 10, "Transcription de la réunion", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for paragraph in text.split("\n\n"):
        pdf.multi_cell(0, 10, paragraph)
        pdf.ln(5)
    pdf.output(filename)
    print(f"✅ PDF sauvegardé sous {filename}")

def save_as_word(text, filename="transcription.docx"):
    doc = Document()
    doc.add_paragraph(text)
    doc.save(filename)
    print(f"✅ Word sauvegardé sous {filename}")

def save_files(text, base_name="transcription"):
    save_as_pdf(text, f"{base_name}.pdf")
    save_as_word(text, f"{base_name}.docx")
