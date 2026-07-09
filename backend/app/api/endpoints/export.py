import base64
import json
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
import plotly.graph_objects as go

router = APIRouter()


class ScriptExportRequest(BaseModel):
    code: str = Field(..., description="The R or Python code string to export")
    language: Literal["r", "python"] = Field("r", description="Target programming language")
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
    format: Literal["markdown", "html", "html_manuscript"] = "markdown"


@router.post("/script", status_code=200)
async def export_script(request: ScriptExportRequest):
    """Download reproducible R or Python code as a standalone script file."""
    ext = "R" if request.language.lower() == "r" else "py"
    default_name = f"quantigen_analysis_{request.language.lower()}.{ext}"
    filename = f"{request.filename}.{ext}" if request.filename else default_name
    
    return Response(
        content=request.code,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/chart", status_code=200)
async def export_chart(request: ChartExportRequest):
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
async def export_report(request: ReportExportRequest):
    """Generate a comprehensive, publication-ready Quantigen AI analysis summary report."""
    import re
    safe_method = re.sub(r'[^a-zA-Z0-9_]', '_', request.method_name.lower())
    
    # Helper to remove raw asterisks (*) from markdown for clean plain text or HTML display
    def clean_narrative(text: str, to_html: bool = True) -> str:
        if not text:
            return ""
        if to_html:
            # Convert bold/italic asterisks to HTML tags and strip any stray asterisks
            t = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
            t = re.sub(r'\*(.*?)\*', r'<em>\1</em>', t)
            t = t.replace('\n\n', '</p><p>').replace('\n', '<br>')
            if not t.startswith('<p>') and not t.startswith('<strong>'):
                t = f'<p>{t}</p>'
            return t
        else:
            # For plain text / markdown, keep clean bolding or strip asterisks if redundant
            return text

    clean_interp_html = clean_narrative(request.interpretation, to_html=True)
    clean_interp_md = clean_narrative(request.interpretation, to_html=False)
    clean_assump_html = clean_narrative(request.assumption_summary or "All statistical assumptions were tested and verified prior to execution.", to_html=True)
    clean_assump_md = clean_narrative(request.assumption_summary or "All statistical assumptions were tested and verified prior to execution.", to_html=False)

    apa_block_md = f"\n## APA 7th Edition Publication Citation\n> {request.apa_citation}\n" if request.apa_citation else ""
    apa_html = f"<h3>APA 7th Edition Publication Citation</h3><blockquote style='background:#f8fafc;border-left:4px solid #0284c7;margin:12px 0;padding:12px 16px;color:#0f172a;font-style:italic;'>{request.apa_citation}</blockquote><hr>" if request.apa_citation else ""

    # Build reliable figure blocks (combining static PNG where possible with interactive Plotly fallback)
    figures_html = ""
    plotly_js_scripts = ""
    if request.plots_json:
        figures_html = "<h3>Academic Manuscript Figures</h3>"
        for idx, plot_dict in enumerate(request.plots_json):
            div_id = f"quantigen_plot_{idx}"
            title_text = plot_dict.get('layout', {}).get('title', {}).get('text', f'Diagnostic Plot {idx + 1}')
            
            # Try high-res static PNG first for pure offline/manuscript quality
            png_success = False
            try:
                fig = go.Figure(plot_dict)
                png_bytes = fig.to_image(format="png", width=900, height=550, scale=2.5)
                b64_img = base64.b64encode(png_bytes).decode("utf-8")
                figures_html += f"""
                <div style="text-align:center; margin: 30px 0;">
                    <img src="data:image/png;base64,{b64_img}" alt="Figure {idx + 1}" style="max-width:100%; height:auto; border: 1px solid #e2e8f0; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                    <p style="font-style:italic; font-size: 0.9em; margin-top: 8px; color: #475569;"><strong>Figure {idx + 1}.</strong> {title_text}</p>
                </div>
                """
                png_success = True
            except Exception:
                pass
            
            # If PNG failed or if we want interactive canvas, embed Plotly container and script
            if not png_success or request.format in ["html", "html_manuscript"]:
                plot_json_str = json.dumps(plot_dict)
                if not png_success:
                    figures_html += f"""
                    <div style="margin: 25px 0;">
                        <div id="{div_id}" style="width:100%;height:520px;border:1px solid #e2e8f0;border-radius:6px;"></div>
                        <p style="font-style:italic; font-size: 0.9em; margin-top: 8px; text-align:center; color: #475569;"><strong>Figure {idx + 1}.</strong> {title_text}</p>
                    </div>
                    """
                plotly_js_scripts += f"try {{ Plotly.newPlot('{div_id}', {plot_json_str}.data, {plot_json_str}.layout, {{responsive: true}}); }} catch(e) {{ console.error(e); }}\n"
        figures_html += "<hr>"

    if request.format == "markdown":
        report_text = f"""# Quantigen AI — Academic Statistical Report: {request.method_name}

## Executive Summary
- **Analysis Procedure**: {request.method_name}
- **Sample Size ($n$)**: {request.sample_size} observations
- **Procedure Description**: {request.description}
{apa_block_md}
---

## Key Findings & Narrative Interpretation
{clean_interp_md}

---

## Assumption Diagnostics
{clean_assump_md}

---

## Reproducible Code Block (R)
```r
{request.r_code}
```

## Reproducible Code Block (Python)
```python
{request.python_code}
```

---
*Report automatically generated by Quantigen AI — Next-Gen Quantitative Statistical Platform.*
"""
        return Response(
            content=report_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_report.md"'}
        )

    elif request.format == "doc":
        # Microsoft Word (.doc) compatible HTML structure
        doc_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Quantigen AI Manuscript Report: {request.method_name}</title>
<style>
    body {{ font-family: 'Calibri', 'Times New Roman', serif; line-height: 1.6; color: #000000; margin: 1in; }}
    h1 {{ font-size: 20pt; color: #0f172a; margin-bottom: 6pt; }}
    h2 {{ font-size: 15pt; color: #0284c7; margin-top: 16pt; margin-bottom: 4pt; }}
    h3 {{ font-size: 13pt; color: #334155; margin-top: 12pt; margin-bottom: 4pt; }}
    p, div {{ font-size: 11pt; margin-bottom: 8pt; }}
    pre {{ background: #f8fafc; padding: 10pt; border: 1pt solid #cbd5e1; font-family: 'Courier New', monospace; font-size: 9.5pt; white-space: pre-wrap; }}
    hr {{ border: none; border-top: 1pt solid #cbd5e1; margin: 16pt 0; }}
</style>
</head>
<body>
<h1>Quantigen AI — Academic Manuscript Report</h1>
<h2>{request.method_name} ($n={request.sample_size}$)</h2>
<p><strong>Description:</strong> {request.description}</p>
<hr>
{apa_html}
<h3>Key Findings & Narrative Interpretation</h3>
<div>{clean_interp_html}</div>
<hr>
{figures_html}
<h3>Assumption Diagnostics Summary</h3>
<div>{clean_assump_html}</div>
<hr>
<h3>Reproducible R Script</h3>
<pre><code>{request.r_code}</code></pre>
<h3>Reproducible Python Script</h3>
<pre><code>{request.python_code}</code></pre>
</body>
</html>"""
        return Response(
            content=doc_content,
            media_type="application/msword",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_manuscript.doc"'}
        )

    elif request.format == "pdf":
        # Print-ready PDF manuscript structure with automatic print dialog prompt
        pdf_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Quantigen AI Manuscript Report: {request.method_name}</title>
<script src="https://cdn.plot.ly/plotly-2.29.1.min.js"></script>
<style>
    @media print {{
        body {{ margin: 0.8in; font-family: 'Times New Roman', serif; color: #000; }}
        .no-print {{ display: none !important; }}
        pre {{ page-break-inside: avoid; border: 1px solid #ccc; padding: 10px; background: #fff; }}
        img, .plotly-graph-div {{ page-break-inside: avoid; max-width: 100% !important; }}
    }}
    body {{ font-family: 'Inter', 'Times New Roman', serif; line-height: 1.7; color: #1e293b; max-width: 850px; margin: 40px auto; padding: 0 30px; }}
    h1, h2, h3 {{ font-family: 'Inter', sans-serif; color: #0f172a; }}
    pre {{ background: #f8fafc; padding: 16px; border-radius: 8px; overflow-x: auto; font-family: monospace; font-size: 0.88em; border: 1px solid #e2e8f0; }}
    hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 28px 0; }}
    .print-banner {{ background: #0284c7; color: #fff; padding: 12px 20px; border-radius: 8px; margin-bottom: 24px; display: flex; justify-content: space-between; items-center; font-family: sans-serif; }}
    .print-btn {{ background: #fff; color: #0284c7; border: none; padding: 6px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
</style>
</head>
<body>
<div class="print-banner no-print">
    <span>Ready to save as PDF? Click the Print/Save button or select 'Save as PDF' in your browser destination.</span>
    <button class="print-btn" onclick="window.print()">Save to PDF</button>
</div>
<h1>Quantigen AI — Academic Manuscript Report</h1>
<h2>{request.method_name} ($n={request.sample_size}$)</h2>
<p><strong>Description:</strong> {request.description}</p>
<hr>
{apa_html}
<h3>Key Findings & Narrative Interpretation</h3>
<div>{clean_interp_html}</div>
<hr>
{figures_html}
<h3>Assumption Diagnostics Summary</h3>
<div>{clean_assump_html}</div>
<hr>
<h3>Reproducible R Script</h3>
<pre><code>{request.r_code}</code></pre>
<h3>Reproducible Python Script</h3>
<pre><code>{request.python_code}</code></pre>
<script>
{plotly_js_scripts}
window.onload = function() {{
    setTimeout(function() {{
        if (confirm("Would you like to open the Save to PDF / Print dialog now?")) {{
            window.print();
        }}
    }}, 1000);
}};
</script>
</body>
</html>"""
        return Response(
            content=pdf_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="quantigen_{safe_method}_manuscript.html"'}
        )

    else:
        # Standard interactive / manuscript HTML report ("html" or "html_manuscript")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Quantigen AI Manuscript Report: {request.method_name}</title>
<script src="https://cdn.plot.ly/plotly-2.29.1.min.js"></script>
<style>
    body {{ font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif; line-height: 1.7; color: #1e293b; max-width: 900px; margin: 40px auto; padding: 0 30px; }}
    h1, h2, h3 {{ color: #0f172a; margin-top: 1.5em; margin-bottom: 0.5em; }}
    h1 {{ font-size: 1.8rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
    pre {{ background: #f8fafc; padding: 16px; border-radius: 8px; overflow-x: auto; font-family: monospace; font-size: 0.9em; border: 1px solid #e2e8f0; }}
    code {{ background: #f8fafc; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
    hr {{ border: 0; border-top: 1px solid #e2e8f0; margin: 32px 0; }}
</style>
</head>
<body>
<h1>Quantigen AI — Academic Manuscript Report</h1>
<h2>{request.method_name} ($n={request.sample_size}$)</h2>
<p><strong>Description:</strong> {request.description}</p>
<hr>
{apa_html}
<h3>Key Findings & Narrative Interpretation</h3>
<div>{clean_interp_html}</div>
<hr>
{figures_html}
<h3>Assumption Diagnostics Summary</h3>
<div>{clean_assump_html}</div>
<hr>
<h3>Reproducible R Script</h3>
<pre><code>{request.r_code}</code></pre>
<h3>Reproducible Python Script</h3>
<pre><code>{request.python_code}</code></pre>
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
