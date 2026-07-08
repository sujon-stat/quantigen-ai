import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_export_chart_png():
    """Verify converting a Plotly figure dictionary to high-res PNG bytes."""
    plot_dict = {
        "data": [{"type": "scatter", "x": [1, 2, 3], "y": [4, 5, 6]}],
        "layout": {"title": {"text": "Test Chart Export"}}
    }
    payload = {
        "plot_json": plot_dict,
        "width": 600,
        "height": 400,
        "scale": 1.5,
        "filename": "my_test_plot"
    }
    response = client.post("/api/v1/export/chart", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert 'filename="my_test_plot.png"' in response.headers["content-disposition"]
    # Verify we got valid PNG header bytes (\x89PNG\r\n\x1a\n)
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_export_report_markdown_with_apa():
    """Verify exporting report as markdown with APA citation."""
    payload = {
        "method_name": "Independent Samples T-Test",
        "description": "Comparison of scores",
        "sample_size": 50,
        "interpretation": "Significant differences observed.",
        "r_code": "t.test(score ~ group, data=df)",
        "python_code": "stats.ttest_ind(g1, g2)",
        "apa_citation": "An independent-samples t-test revealed significant difference, t(48) = 2.45, p = .018.",
        "format": "markdown"
    }
    response = client.post("/api/v1/export/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "APA 7th Edition Publication Citation" in response.text
    assert "t(48) = 2.45, p = .018" in response.text


def test_export_report_html_interactive():
    """Verify exporting report as interactive HTML with plotly.js CDN and plots."""
    payload = {
        "method_name": "One-Way ANOVA",
        "description": "Comparison across 3 departments",
        "sample_size": 90,
        "interpretation": "Significant variance.",
        "r_code": "aov(salary ~ dept, data=df)",
        "python_code": "stats.f_oneway(d1, d2, d3)",
        "apa_citation": "F(2, 87) = 10.12, p < .001.",
        "plots_json": [
            {"data": [{"type": "box", "y": [10, 20, 30]}], "layout": {"title": {"text": "Boxplot"}}}
        ],
        "format": "html"
    }
    response = client.post("/api/v1/export/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "cdn.plot.ly/plotly-2.29.1.min.js" in response.text
    assert "Plotly.newPlot('statmind_plot_0'" in response.text
    assert "APA 7th Edition Publication Citation" in response.text


def test_export_report_html_manuscript():
    """Verify exporting report as manuscript HTML with embedded static high-res PNG image."""
    payload = {
        "method_name": "Logistic Regression",
        "description": "Binary outcome prediction",
        "sample_size": 200,
        "interpretation": "Good model fit.",
        "r_code": "glm(y ~ x, family=binomial)",
        "python_code": "sm.Logit(y, X).fit()",
        "apa_citation": "Chi2(1) = 15.4, p < .001.",
        "plots_json": [
            {"data": [{"type": "scatter", "x": [0, 1], "y": [0, 1]}], "layout": {"title": {"text": "ROC Curve"}}}
        ],
        "format": "html_manuscript"
    }
    response = client.post("/api/v1/export/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Academic Manuscript Report" in response.text
    assert "data:image/png;base64," in response.text
    assert "Figure 1." in response.text
