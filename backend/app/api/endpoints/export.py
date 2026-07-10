import base64
import json
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
import plotly.graph_objects as go

router = APIRouter()


class ScriptExportRequest(BaseModel):
    code: str = Field(..., description="The R, Python, or RMarkdown code string to export")
    language: str = Field("r", description="Target programming language (r, python, rmd)")
    filename: Optional[str] = Field(None, description="Desired download filename without extension")


class ChartExportRequest(BaseModel):
    plot_json: Dict[str, Any] = Field(..., description="The Plotly JSON or figure dictionary to convert to image")
    width: int = Field(1000, description="Image width in pixels")
    height: int = Field(600, description="Image height in pixels")
    scale: float = Field(3.0, description="Scale factor (3.0 for 300 DPI high-res manuscript quality)")
    filename: Optional[str] = Field("statmind_chart", description="Desired download filename without extension")


class ReportExportRequest(BaseModel):
    method_name: str
    description: str
    sample_size: int
    interpretation: str
    r_code: str
    python_code: str
    apa_citation: Optional[str] = None
    assumption_summary: Optional[str] = None
    plots_json: Optional[List[Dict[str, Any]]] = None
    format: Literal["markdown", "html", "html_manuscript", "doc", "pdf"] = "markdown"


class PortfolioItemConfig(BaseModel):
    history_id: str
    include_table: bool = True
    include_graph: bool = True
    include_narrative: bool = True
    include_code: bool = True
    preferred_graph_type: str = "default"


class PortfolioItemRequest(BaseModel):
    history_id: str
    method_name: str
    description: str
    sample_size: int
    interpretation: str
    r_code: str
    python_code: str
    apa_citation: Optional[str] = None
    assumption_summary: Optional[str] = None
    plots_json: Optional[List[Dict[str, Any]]] = None
    main_results: Optional[Dict[str, Any]] = None
    effect_sizes: Optional[Dict[str, Any]] = None
    config: PortfolioItemConfig


class PortfolioExportRequest(BaseModel):
    title: str = "Quantigen AI Academic Multi-Analysis Portfolio"
    items: List[PortfolioItemRequest]
    format: Literal["pdf", "doc", "html", "rmarkdown"] = "pdf"


@router.post("/script", status_code=200)
async def export_script(request: ScriptExportRequest):
    """Download reproducible R, Python, or RMarkdown code as a standalone script file."""
    lang = request.language.lower()
    if lang == "rmd":
        ext = "Rmd"
    elif lang == "r":
        ext = "R"
    else:
        ext = "py"
    default_name = f"quantigen_analysis_{lang}.{ext}"
    filename = f"{request.filename}.{ext}" if request.filename else default_name
    
    return Response(
        content=request.code,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/chart", status_code=200)
def export_chart(request: ChartExportRequest):
    """Export a Plotly chart dictionary to a high-resolution PNG image (image/png via kaleido) suitable for manuscripts."""
    fig = go.Figure(request.plot_json)
    png_bytes = fig.to_image(format="png", width=request.width, height=request.height, scale=request.scale)
    
    filename = f"{request.filename or 'quantigen_chart'}.png"
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/report", status_code=200)
def export_report(request: ReportExportRequest):
    """Generate a comprehensive, publication-ready Quantigen AI analysis summary report."""
    import re
    from backend.app.services.visualization.themes import format_ai_label
    
    # Strip any stored ($n=...$) or $n=...$ or $ from method_name
    clean_method_name = re.sub(r'\s*\(\$n=[0-9,]+\$\)', '', request.method_name)
    clean_method_name = re.sub(r'\s*\(n\s*=\s*[0-9,]+\)', '', clean_method_name).replace('$', '').strip()
    safe_method = re.sub(r'[^a-zA-Z0-9_]', '_', clean_method_name.lower())
    
    # Helper to remove raw asterisks (*) and LaTeX dollar math ($) from markdown for clean plain text or HTML display
    def clean_narrative(text: str, to_html: bool = True) -> str:
        if not text:
            return ""
        # 1. Strip parenthesized and raw LaTeX math $...$ notation to natural human readable text without dollar signs
        t = re.sub(r'\(\$n=([0-9,]+)\$\)', r'(n = \1)', text)
        t = re.sub(r'\$n=([0-9,]+)\$', r'(n = \1)', t)
        t = re.sub(r'\(\$p_\{adj\}\s*=\s*([0-9.]+)\$\)', r'(p_adj = \1)', t)
        t = re.sub(r'\$p_\{adj\}\s*=\s*([0-9.]+)\$', r'(p_adj = \1)', t)
        t = re.sub(r'\(\$p\s*=\s*([0-9.]+)\$\)', r'(p = \1)', t)
        t = re.sub(r'\$p\s*=\s*([0-9.]+)\$', r'(p = \1)', t)
        t = re.sub(r'\$([A-Za-z0-9_\\^(),+\s=.+-]+)\$', r'\1', t)
        t = t.replace('\\eta^2', 'η²').replace('\\omega^2', 'ω²').replace('\\chi^2', 'χ²').replace('\\rho', 'ρ').replace('\\epsilon^2', 'ε²').replace('\\beta', 'β').replace('\\alpha', 'α')
        t = re.sub(r'\^([0-9]+)', r'^\1', t).replace('R^2', 'R²').replace('r^2', 'r²')
        t = t.replace('((n = ', '(n = ').replace('))', ')').replace('$', '')

        if to_html:
            # Convert bold/italic asterisks to HTML tags and strip any stray asterisks
            t = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', t)
            t = re.sub(r'\*(.*?)\*', r'<em>\1</em>', t)
            t = t.replace('\n\n', '</p><p>').replace('\n', '<br>')
            if not t.startswith('<p>') and not t.startswith('<strong>'):
                t = f'<p>{t}</p>'
            return t
        else:
            # For plain text / markdown, keep clean bolding or strip asterisks if redundant
            return t

    clean_interp_html = clean_narrative(request.interpretation, to_html=True)
    clean_interp_md = clean_narrative(request.interpretation, to_html=False)
    clean_assump_html = clean_narrative(request.assumption_summary or "All statistical assumptions were tested and verified prior to execution.", to_html=True)
    clean_assump_md = clean_narrative(request.assumption_summary or "All statistical assumptions were tested and verified prior to execution.", to_html=False)

    apa_block_md = f"\n## APA 7th Edition Publication Citation\n> {request.apa_citation}\n" if request.apa_citation else ""
    apa_html = f"<h3>APA 7th Edition Publication Citation</h3><blockquote style='background:#f8fafc;border-left:4px solid #0284c7;margin:12px 0;padding:12px 16px;color:#0f172a;font-style:italic;'>{request.apa_citation}</blockquote><hr>" if request.apa_citation else ""

    # Build reliable figure blocks (combining static PNG where possible with interactive Plotly fallback)
    figures_html = ""
    figures_doc_html = ""
    doc_mime_parts = []
    plotly_js_scripts = ""
    if request.plots_json:
        figures_html = "<h3>Academic Manuscript Figures</h3>"
        figures_doc_html = "<h3>Academic Manuscript Figures</h3>"
        for idx, plot_dict in enumerate(request.plots_json):
            div_id = f"quantigen_plot_{idx}"
            title_text = plot_dict.get('layout', {}).get('title', {}).get('text', f'Diagnostic Plot {idx + 1}')
            # Clean title text if it contains bolding or HTML tags from plotly, replacing line breaks with separators
            pre_clean = re.sub(r'<br\s*/?>', ' - ', str(title_text), flags=re.IGNORECASE)
            raw_title = re.sub(r'<[^>]+>', '', pre_clean).replace('$', '').strip()
            # Upgrade raw phrases like "Category Counts for player_id" or "Distribution of age" to publication AI labels
            if "Category Counts for " in raw_title:
                var_name = raw_title.replace("Category Counts for ", "").strip()
                clean_title = f"Demographic & Categorical Frequency of {format_ai_label(var_name)}"
            elif "Distribution of " in raw_title:
                var_name = raw_title.replace("Distribution of ", "").strip()
                clean_title = f"Population Distribution of {format_ai_label(var_name)}"
            else:
                clean_title = format_ai_label(raw_title) if any(c.islower() for c in raw_title) else raw_title
            
            # Try high-res static PNG first for pure offline/manuscript quality
            png_success = False
            try:
                fig = go.Figure(plot_dict)
                png_bytes = fig.to_image(format="png", width=900, height=550, scale=2.5)
                b64_img = base64.b64encode(png_bytes).decode("utf-8")
                
                # For standard HTML / Markdown embedding
                figures_html += f"""
                <div style="text-align:center; margin: 30px 0;">
                    <img src="data:image/png;base64,{b64_img}" alt="Figure {idx + 1}" style="max-width:100%; height:auto; border: 1px solid #e2e8f0; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                    <p style="font-style:italic; font-size: 0.9em; margin-top: 8px; color: #475569;"><strong>Figure {idx + 1}.</strong> {clean_title}</p>
                </div>
                """
                
                # For Microsoft Word (.doc) MHTML embedding with cid reference
                img_cid = f"quantigen_plot_{idx}.png"
                figures_doc_html += f"""
                <div style="text-align:center; margin: 24pt 0;">
                    <img src="cid:{img_cid}" width="600" style="width:6in; height:auto; border:1pt solid #cbd5e1; display:block; margin: 0 auto;">
                    <p style="font-style:italic; font-size:10pt; margin-top:6pt; color:#475569;"><strong>Figure {idx + 1}.</strong> {clean_title}</p>
                </div>
                """
                doc_mime_parts.append(f"""------=_NextPart_Quantigen_MHTML_Boundary
Content-Type: image/png
Content-Transfer-Encoding: base64
Content-ID: <{img_cid}>
Content-Location: {img_cid}

{b64_img}""")
                png_success = True
            except Exception as e:
                import logging
                logging.getLogger("quantigen_export").warning(f"Static PNG export failed for plot {idx}: {e}")
            
            # If PNG failed or if we want interactive canvas, embed Plotly container and script
            if not png_success or request.format in ["html", "html_manuscript"]:
                plot_json_str = json.dumps(plot_dict)
                if not png_success:
                    figures_html += f"""
                    <div style="margin: 25px 0;">
                        <div id="{div_id}" style="width:100%;height:520px;border:1px solid #e2e8f0;border-radius:6px;"></div>
                        <p style="font-style:italic; font-size: 0.9em; margin-top: 8px; text-align:center; color: #475569;"><strong>Figure {idx + 1}.</strong> {clean_title}</p>
                    </div>
                    """
                    figures_doc_html += f"""
                    <div style="margin: 25px 0;">
                        <p style="font-style:italic; font-size:10pt; color:#475569;"><strong>Figure {idx + 1}.</strong> {clean_title} (Interactive chart viewable in HTML version)</p>
                    </div>
                    """
                plotly_js_scripts += f"try {{ Plotly.newPlot('{div_id}', {plot_json_str}.data, {plot_json_str}.layout, {{responsive: true}}); }} catch(e) {{ console.error(e); }}\n"
        figures_html += "<hr>"
        figures_doc_html += "<hr>"

    if request.format == "markdown":
        report_text = f"""# Quantigen AI — Academic Statistical Report: {clean_method_name}

## Executive Summary
- **Analysis Procedure**: {clean_method_name}
- **Sample Size (n)**: {request.sample_size:,} observations
- **Procedure Description**: {request.description}
{apa_block_md}
---

## Key Findings & Narrative Interpretation
{clean_interp_md}

---

## Assumption Diagnostics
{clean_assump_md}

---
*Report automatically generated by Quantigen AI — Next-Gen Quantitative Statistical Platform.*
"""
        return Response(
            content=report_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_report.md"'}
        )

    elif request.format == "doc":
        # Microsoft Word (.doc) single-file MHTML (multipart/related) structure with embedded graphs & exact page setup
        doc_html_part = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta charset="utf-8">
<title>Quantigen AI Manuscript Report: {clean_method_name}</title>
<style>
    @page Section1 {{
        size: 8.5in 11.0in;
        margin: 1.0in 1.0in 1.0in 1.0in;
        mso-header-margin: 0.5in;
        mso-footer-margin: 0.5in;
        mso-paper-source: 0;
    }}
    div.Section1 {{
        page: Section1;
    }}
    body {{ font-family: 'Calibri', 'Times New Roman', serif; line-height: 1.6; color: #000000; }}
    h1 {{ font-size: 20pt; color: #0f172a; margin-bottom: 6pt; }}
    h2 {{ font-size: 15pt; color: #0284c7; margin-top: 16pt; margin-bottom: 4pt; }}
    h3 {{ font-size: 13pt; color: #334155; margin-top: 12pt; margin-bottom: 4pt; }}
    p, div {{ font-size: 11pt; margin-bottom: 8pt; }}
    pre {{ background: #f8fafc; padding: 10pt; border: 1pt solid #cbd5e1; font-family: 'Courier New', monospace; font-size: 9.5pt; white-space: pre-wrap; }}
    hr {{ border: none; border-top: 1pt solid #cbd5e1; margin: 16pt 0; }}
</style>
</head>
<body>
<div class="Section1">
<h1>Quantigen AI — Academic Manuscript Report</h1>
<h2>{clean_method_name} (n = {request.sample_size:,})</h2>
<p><strong>Description:</strong> {request.description}</p>
<hr>
{apa_html}
<h3>Key Findings & Narrative Interpretation</h3>
<div>{clean_interp_html}</div>
<hr>
{figures_doc_html}
<h3>Assumption Diagnostics Summary</h3>
<div>{clean_assump_html}</div>
</div>
</body>
</html>"""

        mime_attachments = "\n".join(doc_mime_parts)
        doc_mhtml = f"""MIME-Version: 1.0
Content-Type: multipart/related; boundary="----=_NextPart_Quantigen_MHTML_Boundary"

------=_NextPart_Quantigen_MHTML_Boundary
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 8bit
Content-Location: file:///C:/quantigen_manuscript.htm

{doc_html_part}
{mime_attachments}
------=_NextPart_Quantigen_MHTML_Boundary--"""

        return Response(
            content=doc_mhtml,
            media_type="application/msword",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_manuscript.doc"'}
        )

    elif request.format == "pdf":
        from fpdf import FPDF
        import tempfile
        import os

        def safe_pdf_text(text: Any) -> str:
            if not text:
                return ""
            text = str(text)
            replacements = {
                '—': '--',
                '–': '-',
                '“': '"',
                '”': '"',
                '‘': "'",
                '’': "'",
                'χ²': 'Chi2',
                'η²': 'eta2',
                'ω²': 'omega2',
                'ε²': 'epsilon2',
                'R²': 'R2',
                'r²': 'r2',
                '…': '...',
                '•': '*'
            }
            for k, v in replacements.items():
                text = text.replace(k, v)
            return text.encode('latin-1', 'replace').decode('latin-1')

        class ManuscriptPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(100, 116, 139) # slate-500
                self.cell(0, 8, safe_pdf_text("Quantigen AI -- Academic Manuscript Report"), align="R", new_x="LMARGIN", new_y="NEXT")
                self.ln(6)
                
            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(148, 163, 184) # slate-400
                self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

        pdf = ManuscriptPDF(orientation="P", unit="mm", format="A4")
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        
        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(15, 23, 42) # slate-900
        pdf.multi_cell(0, 8, safe_pdf_text("Quantigen AI -- Academic Manuscript Report"), align="C")
        pdf.ln(3)
        
        # Method & Sample Size
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(2, 132, 199) # sky-600
        pdf.multi_cell(0, 7, safe_pdf_text(f"{clean_method_name} (n = {request.sample_size:,})"))
        pdf.ln(2)
        
        # Description
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85) # slate-700
        pdf.multi_cell(0, 6, safe_pdf_text(f"Description: {request.description}"))
        pdf.ln(4)
        
        # APA Citation Box
        if request.apa_citation:
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(2, 132, 199)
            pdf.set_font("Helvetica", "BI", 9.5)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(0, 6, safe_pdf_text(f"APA 7th Citation: {request.apa_citation}"), border=1, fill=True)
            pdf.ln(5)
            
        # Key Findings & Narrative Interpretation
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, safe_pdf_text("Key Findings & Narrative Interpretation"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 6, safe_pdf_text(clean_interp_md))
        pdf.ln(6)
        
        # Figures (if any)
        if request.plots_json:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 8, safe_pdf_text("Academic Manuscript Figures"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
            for idx, plot_dict in enumerate(request.plots_json):
                title_text = plot_dict.get('layout', {}).get('title', {}).get('text', f'Diagnostic Plot {idx + 1}')
                pre_clean = re.sub(r'<br\s*/?>', ' - ', str(title_text), flags=re.IGNORECASE)
                raw_title = re.sub(r'<[^>]+>', '', pre_clean).replace('$', '').strip()
                if "Category Counts for " in raw_title:
                    var_name = raw_title.replace("Category Counts for ", "").strip()
                    clean_title = f"Demographic & Categorical Frequency of {format_ai_label(var_name)}"
                elif "Distribution of " in raw_title:
                    var_name = raw_title.replace("Distribution of ", "").strip()
                    clean_title = f"Empirical Normal Distribution & KDE Fit of {format_ai_label(var_name)}"
                else:
                    clean_title = raw_title

                try:
                    fig = go.Figure(plot_dict)
                    fig.update_layout(
                        title=dict(text=clean_title, font=dict(family="Arial, sans-serif", size=14, color="#0f172a")),
                        paper_bgcolor='white',
                        plot_bgcolor='white',
                        width=800,
                        height=480
                    )
                    png_data = fig.to_image(format="png", width=800, height=480, scale=2)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                        tmp_img.write(png_data)
                        tmp_path = tmp_img.name
                        
                    if pdf.get_y() > 180:
                        pdf.add_page()
                        
                    pdf.set_font("Helvetica", "B", 10.5)
                    pdf.set_text_color(30, 41, 59)
                    pdf.cell(0, 7, safe_pdf_text(f"Figure {idx + 1}: {clean_title}"), new_x="LMARGIN", new_y="NEXT")
                    pdf.image(tmp_path, w=170)
                    pdf.ln(5)
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                except Exception as e:
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.cell(0, 6, safe_pdf_text(f"[Figure {idx + 1} ({clean_title}) included in interactive HTML/doc formats]"), new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(4)
                    
        # Assumption Diagnostics
        if pdf.get_y() > 230:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, safe_pdf_text("Assumption Diagnostics Summary"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 6, safe_pdf_text(clean_assump_md))
        
        pdf_bytes = bytes(pdf.output())
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_manuscript.pdf"'}
        )

    else:
        # Standard interactive / manuscript HTML report ("html" or "html_manuscript")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Quantigen AI Manuscript Report: {clean_method_name}</title>
<script src="https://cdn.plot.ly/plotly-2.29.1.min.js"></script>
<style>
    body {{ font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif; line-height: 1.7; color: #1e293b; max-width: 900px; margin: 40px auto; padding: 0 30px; }}
    h1, h2, h3 {{ color: #0f172a; margin-top: 1.5em; margin-bottom: 0.5em; }}
    h1 {{ font-size: 1.8rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
    code {{ background: #f8fafc; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
    hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 32px 0; }}
</style>
</head>
<body>
<h1>Quantigen AI — Academic Manuscript Report</h1>
<h2>{clean_method_name} (n = {request.sample_size:,})</h2>
<p><strong>Description:</strong> {request.description}</p>
<hr>
{apa_html}
<h3>Key Findings & Narrative Interpretation</h3>
<div>{clean_interp_html}</div>
<hr>
{figures_html}
<h3>Assumption Diagnostics Summary</h3>
<div>{clean_assump_html}</div>
<script>
{plotly_js_scripts}
</script>
</body>
</html>"""
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_report.html"'}
        )


@router.post("/portfolio", status_code=200)
def export_portfolio(request: PortfolioExportRequest):
    """Compile and download a multi-run portfolio in PDF, Word (.doc/.docx), HTML, or RMarkdown (.Rmd)."""
    import re
    import tempfile
    import os
    from fpdf import FPDF
    from backend.app.services.visualization.themes import format_ai_label

    safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', request.title.lower().strip() or "quantigen_portfolio")

    # Helper to clean text/markdown
    def clean_narrative(text: str, to_html: bool = True) -> str:
        if not text:
            return ""
        t = re.sub(r'\(\$n=([0-9,]+)\$\)', r'(n = \1)', text)
        t = re.sub(r'\$n=([0-9,]+)\$', r'(n = \1)', t)
        t = re.sub(r'\(\$p_\{adj\}\s*=\s*([0-9.]+)\$\)', r'(p_adj = \1)', t)
        t = re.sub(r'\$p_\{adj\}\s*=\s*([0-9.]+)\$', r'(p_adj = \1)', t)
        t = re.sub(r'\(\$p\s*=\s*([0-9.]+)\$\)', r'(p = \1)', t)
        t = re.sub(r'\$p\s*=\s*([0-9.]+)\$', r'(p = \1)', t)
        t = re.sub(r'\$([A-Za-z0-9_\\^(),+\s=.+-]+)\$', r'\1', t)
        t = t.replace('\\eta^2', 'η²').replace('\\omega^2', 'ω²').replace('\\chi^2', 'χ²').replace('\\rho', 'ρ').replace('\\epsilon^2', 'ε²').replace('\\beta', 'β').replace('\\alpha', 'α')
        t = re.sub(r'\^([0-9]+)', r'^\1', t).replace('R^2', 'R²').replace('r^2', 'r²')
        t = t.replace('((n = ', '(n = ').replace('))', ')').replace('$', '')
        if to_html:
            t = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', t)
            t = re.sub(r'\*(.*?)\*', r'<em>\1</em>', t)
            t = t.replace('\n\n', '</p><p>').replace('\n', '<br>')
            if not t.startswith('<p>') and not t.startswith('<strong>'):
                t = f'<p>{t}</p>'
            return t
        else:
            return t

    if request.format == "rmarkdown":
        # Generate pristine RMarkdown (.Rmd) file for direct knitting in RStudio
        rmd_lines = [
            "---",
            f'title: "{request.title}"',
            'author: "Quantigen AI — Automated Statistical Engine"',
            f'date: "`r Sys.Date()`"',
            "output:",
            "  pdf_document:",
            "    toc: true",
            "    number_sections: true",
            "  word_document:",
            "    toc: true",
            "  html_document:",
            "    toc: true",
            "    toc_float: true",
            "    theme: united",
            "---",
            "",
            "```{r setup, include=FALSE}",
            "knitr::opts_chunk$set(echo = TRUE, warning = FALSE, message = FALSE, fig.width = 8, fig.height = 5.5, dpi = 300)",
            "library(ggplot2)",
            "library(dplyr)",
            "```",
            "",
            "# Executive Summary",
            "",
            f"This comprehensive statistical portfolio compiles `{len(request.items)}` distinct analytical runs executed via **Quantigen AI**. All models have been automatically validated against underlying distributional assumptions with exact Type I error control ($\alpha = 0.05$).",
            ""
        ]

        for i, item in enumerate(request.items, 1):
            cfg = item.config
            clean_name = re.sub(r'\s*\(\$n=[0-9,]+\$\)', '', item.method_name).replace('$', '').strip()
            rmd_lines.append(f"# Analysis {i}: {clean_name} (N = {item.sample_size:,})")
            rmd_lines.append(f"\n**Method Description:** {item.description}\n")

            if item.apa_citation and cfg.include_narrative:
                rmd_lines.append("## APA 7th Edition Publication Citation")
                rmd_lines.append(f"> {item.apa_citation}\n")

            if cfg.include_narrative and item.interpretation:
                rmd_lines.append("## Narrative Interpretation & Findings")
                clean_interp = clean_narrative(item.interpretation, to_html=False)
                rmd_lines.append(f"{clean_interp}\n")

            if cfg.include_table and (item.main_results or item.effect_sizes):
                rmd_lines.append("## Core Statistical Summary Table")
                rmd_lines.append("| Metric / Parameter | Value / Output |")
                rmd_lines.append("| :--- | :--- |")
                if item.main_results:
                    for k, v in item.main_results.items():
                        if not isinstance(v, (dict, list)):
                            rmd_lines.append(f"| **{k.replace('_', ' ').title()}** | `{v}` |")
                if item.effect_sizes:
                    for k, v in item.effect_sizes.items():
                        if not isinstance(v, (dict, list)):
                            rmd_lines.append(f"| **Effect Size ({k.replace('_', ' ').title()})** | `{v}` |")
                rmd_lines.append("")

            if cfg.include_code and item.r_code:
                rmd_lines.append("## 100% Reproducible R Script & Visualizations")
                chunk_id = re.sub(r'[^a-zA-Z0-9]', '', item.history_id) or f"chunk_{i}"
                rmd_lines.append(f"```{{r {chunk_id}}}")
                rmd_lines.append("# To run this script directly on your own dataset, set your dataset path inside read.csv()")
                rmd_lines.append(item.r_code)
                rmd_lines.append("```")
                rmd_lines.append("")

        rmd_content = "\n".join(rmd_lines)
        return Response(
            content=rmd_content,
            media_type="text/plain;charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.Rmd"'}
        )

    elif request.format == "pdf":
        # Multi-page FPDF Portfolio
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        def safe_pdf_text(txt: str) -> str:
            if not txt:
                return ""
            repl = {
                '–': '-', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'", '…': '...',
                'χ²': 'Chi-Square', 'χ': 'Chi', 'η²': 'eta^2', 'ω²': 'omega^2',
                'ε²': 'epsilon^2', 'R²': 'R^2', 'r²': 'r^2', 'ρ': 'rho',
                'α': 'alpha', 'β': 'beta', '≤': '<=', '≥': '>=', '±': '+/-',
                'p < .001': 'p < .001', 'p_adj': 'p_adj'
            }
            res = txt
            for k, v in repl.items():
                res = res.replace(k, v)
            return res.encode('latin-1', 'replace').decode('latin-1')

        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 12, safe_pdf_text(request.title), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 8, safe_pdf_text("Compiled via Quantigen AI — Hardened Inference & Assumption Shield"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)

        for i, item in enumerate(request.items, 1):
            cfg = item.config
            clean_name = re.sub(r'\s*\(\$n=[0-9,]+\$\)', '', item.method_name).replace('$', '').strip()
            
            if pdf.get_y() > 220:
                pdf.add_page()
                
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(2, 132, 199)
            pdf.cell(0, 10, safe_pdf_text(f"Section {i}: {clean_name} (N = {item.sample_size:,})"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(0, 6, safe_pdf_text(item.description))
            pdf.ln(4)

            if item.apa_citation and cfg.include_narrative:
                pdf.set_font("Helvetica", "I", 10)
                pdf.set_fill_color(248, 250, 252)
                pdf.set_text_color(15, 23, 42)
                pdf.multi_cell(0, 6, safe_pdf_text(f"APA 7th Citation: {item.apa_citation}"), border=1, fill=True)
                pdf.ln(4)

            if cfg.include_narrative and item.interpretation:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 7, safe_pdf_text("Narrative Findings & Interpretation"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 41, 59)
                clean_interp = clean_narrative(item.interpretation, to_html=False)
                pdf.multi_cell(0, 6, safe_pdf_text(clean_interp))
                pdf.ln(4)

            if cfg.include_graph and item.plots_json and len(item.plots_json) > 0:
                plot_dict = item.plots_json[0]
                title_text = plot_dict.get('layout', {}).get('title', {}).get('text', f'Figure {i}')
                clean_title = re.sub(r'<[^>]+>', '', str(title_text)).replace('$', '').strip()
                try:
                    fig = go.Figure(plot_dict)
                    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', width=800, height=450)
                    png_data = fig.to_image(format="png", width=800, height=450, scale=2)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                        tmp_img.write(png_data)
                        tmp_path = tmp_img.name
                    if pdf.get_y() > 175:
                        pdf.add_page()
                    pdf.set_font("Helvetica", "B", 10.5)
                    pdf.cell(0, 7, safe_pdf_text(f"Figure {i}: {clean_title}"), new_x="LMARGIN", new_y="NEXT")
                    pdf.image(tmp_path, w=170)
                    pdf.ln(6)
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                except Exception:
                    pass

            pdf.ln(8)

        pdf_bytes = bytes(pdf.output())
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'}
        )

    else:
        # Multi-section HTML or DOC
        is_doc = (request.format == "doc")
        body_parts = [f"<h1 style='text-align:center;color:#0f172a;'>{request.title}</h1><p style='text-align:center;color:#64748b;font-style:italic;'>Compiled via Quantigen AI Academic Suite</p><hr>"]
        
        for i, item in enumerate(request.items, 1):
            cfg = item.config
            clean_name = re.sub(r'\s*\(\$n=[0-9,]+\$\)', '', item.method_name).replace('$', '').strip()
            page_break = "style='page-break-before:always;'" if is_doc and i > 1 else "style='margin-top:50px;border-top:3px solid #0284c7;padding-top:20px;'"
            
            section_html = f"<div {page_break}><h2 style='color:#0284c7;'>{i}. {clean_name} (N = {item.sample_size:,})</h2><p>{item.description}</p>"
            
            if item.apa_citation and cfg.include_narrative:
                section_html += f"<blockquote style='background:#f8fafc;border-left:4px solid #059669;padding:12px;font-style:italic;'><strong>APA Citation:</strong> {item.apa_citation}</blockquote>"
                
            if cfg.include_narrative and item.interpretation:
                section_html += f"<h3>Narrative Findings</h3><div>{clean_narrative(item.interpretation, to_html=True)}</div>"
                
            if cfg.include_table and (item.main_results or item.effect_sizes):
                section_html += "<h3 style='margin-top:20px;'>Summary Statistics Table</h3><table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:0.9em;'><tr style='background:#f1f5f9;'><th>Parameter</th><th>Value</th></tr>"
                if item.main_results:
                    for k, v in item.main_results.items():
                        if not isinstance(v, (dict, list)):
                            section_html += f"<tr><td><strong>{k.replace('_', ' ').title()}</strong></td><td>{v}</td></tr>"
                section_html += "</table>"
                
            if cfg.include_graph and item.plots_json and len(item.plots_json) > 0:
                plot_dict = item.plots_json[0]
                title_text = plot_dict.get('layout', {}).get('title', {}).get('text', f'Figure {i}')
                clean_title = re.sub(r'<[^>]+>', '', str(title_text)).replace('$', '').strip()
                try:
                    fig = go.Figure(plot_dict)
                    png_bytes = fig.to_image(format="png", width=850, height=500, scale=2)
                    b64_img = base64.b64encode(png_bytes).decode("utf-8")
                    section_html += f"<div style='text-align:center;margin:25px 0;'><img src='data:image/png;base64,{b64_img}' style='max-width:100%;height:auto;border:1px solid #ccc;'><p><em><strong>Figure {i}.</strong> {clean_title}</em></p></div>"
                except Exception:
                    pass
                    
            section_html += "</div>"
            body_parts.append(section_html)

        ext = "doc" if is_doc else "html"
        mime = "application/msword" if is_doc else "text/html;charset=utf-8"
        full_doc = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{request.title}</title><style>body{{font-family:Inter,Arial,sans-serif;line-height:1.6;color:#1e293b;max-width:900px;margin:40px auto;padding:20px;}} table th, table td{{padding:8px 12px;text-align:left;}}</style></head><body>{''.join(body_parts)}</body></html>"
        return Response(
            content=full_doc,
            media_type=mime,
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.{ext}"'}
        )
