import streamlit as st
from fpdf import FPDF
import google.generativeai as genai
from PIL import Image
import datetime
import os
import re


# Setup Gemini API
genai.configure(api_key="AIzaSyCObIxNQoZsf7IwvI-bcOS1vf-rt6-ZgY8")

# Generate proposal content using Gemini
def generate_proposal_content(client_name, project_title, project_scope, timeline, budget):
    prompt = f"""
    Generate a professional business proposal with the following structure:
    1. Introduction
    2. Scope of Work
    3. Timeline
    4. Pricing
    5. Conclusion
    
    Details:
    - Client: {client_name}
    - Project Title: {project_title}
    - Scope: {project_scope}
    - Timeline: {timeline}
    - Budget: {budget}
    Use markdown-like section titles (e.g., ## Introduction)
    """
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

# Custom PDF with styling and optional logo
class StyledPDF(FPDF):
    def header(self):
        self.set_line_width(0.5)
        self.rect(10, 10, 190, 277)  # Page border

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 30, 120)
        self.ln(8)
        self.cell(0, 10, title, ln=True, align="L")
        self.ln(4)

    def chapter_body(self, body):
        self.set_font("Helvetica", "", 12)
        self.set_text_color(0, 0, 0)

        bold_label_pattern = r"\*\*(.+?):\*\*"
        segments = re.split(bold_label_pattern, body)
        i = 0
        while i < len(segments):
            if i % 2 == 1:
                label = segments[i].strip()
                self.set_font("Helvetica", "B", 12)
                self.cell(25, 10, f"{label}:", ln=False)  # Fixed width for label
                self.set_font("Helvetica", "", 12)
            else:
                text = segments[i].strip()
                # Wrap text in multi_cell with max width = page width - margins - label width
                self.multi_cell(0, 10, f" {text}")
            i += 1
        self.ln(2)

    def insert_image(self, image_path):
        self.image(image_path, x=150, y=250, w=40)


def parse_proposal_and_generate_pdf(content, filename, logo_file=None):
    pdf = StyledPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)
    pdf.add_page()

    current_paragraph_lines = []

    def flush_paragraph():
        if current_paragraph_lines:
            paragraph = " ".join(current_paragraph_lines).strip()
            if paragraph:
                pdf.chapter_body(paragraph)
            current_paragraph_lines.clear()

    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()

        # Handle markdown-style heading (## Heading)
        if line.startswith("## "):
            flush_paragraph()
            heading = line[3:].strip()
            pdf.chapter_title(heading)

        # Empty line means paragraph break
        elif line == "":
            flush_paragraph()

        # Normal paragraph line
        else:
            # Remove any leftover * or markdown if mistakenly present
            clean_line = line.replace("*", "").strip()
            current_paragraph_lines.append(clean_line)

    flush_paragraph()

    if logo_file:
        logo_path = "temp_logo.png"
        logo = Image.open(logo_file)
        logo.save(logo_path)
        pdf.insert_image(logo_path)
        os.remove(logo_path)

    pdf.output(filename)
    return filename

# Streamlit UI
st.title("📝 Proposal Generator AI")
st.header("Craft a Professional Proposal in Minutes!")
st.subheader("Powered by SOLIVOX AI")

with st.form("proposal_form"):
    client_name = st.text_input("Client Name")
    project_title = st.text_input("Project Title")
    project_scope = st.text_area("Project Scope")
    timeline = st.text_input("Timeline (e.g., 4 weeks)")
    budget = st.text_input("Estimated Budget (e.g., $1500)")
    logo_file = st.file_uploader("Upload Client Logo or Signature (PNG/JPG)", type=["png", "jpg", "jpeg"])

    submitted = st.form_submit_button("Generate Proposal")

if submitted:
    with st.spinner("Crafting your proposal with style..."):
        content = generate_proposal_content(client_name, project_title, project_scope, timeline, budget)
        filename = f"{client_name.replace(' ', '_')}_Proposal.pdf"
        parse_proposal_and_generate_pdf(content, filename, logo_file)

        st.success("✅ Styled proposal PDF generated!")
        with open(filename, "rb") as file:
            st.download_button(
                label="📥 Download Proposal PDF",
                data=file,
                file_name=filename,
                mime="application/pdf"
            )

