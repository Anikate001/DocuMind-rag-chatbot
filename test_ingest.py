from fpdf import FPDF
from ingest import ingest_pdf

print("Creating dummy PDF...")
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=15)
pdf.cell(200, 10, txt="Python is a popular programming language.", ln=1, align="C")
pdf.output("dummy_knowledge.pdf")
print("PDF created.")

print("Ingesting PDF...")
try:
    with open("dummy_knowledge.pdf", "rb") as f:
        file_bytes = f.read()
    
    result = ingest_pdf(file_bytes, "dummy_knowledge.pdf")
    print("Ingestion successful:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
