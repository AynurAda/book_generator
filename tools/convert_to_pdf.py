#!/usr/bin/env python
"""Convert deep research results to PDF."""

import json
import markdown
from weasyprint import HTML

with open('deep_research_results.json') as f:
    data = json.load(f)

html = """
<html>
<head>
<style>
body { font-family: Georgia, serif; margin: 40px; line-height: 1.7; }
h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
h2 { color: #34495e; margin-top: 30px; }
h3 { color: #555; margin-top: 20px; }
.metadata { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 0.9em; }
ul, ol { margin-left: 20px; }
li { margin-bottom: 8px; }
p { margin-bottom: 12px; }
</style>
</head>
<body>
<h1>Gemini Deep Research Results</h1>
"""

for r in data.get('results', []):
    if 'error' in r:
        html += f"<h2>{r.get('query_name')}</h2><p style='color:red;'>Error: {r['error']}</p>"
    else:
        output_html = markdown.markdown(r.get('output', ''), extensions=['tables', 'fenced_code'])
        html += f"""
        <h2>Query: {r.get('query_name')}</h2>
        <div class="metadata">
            Duration: {r.get('elapsed_seconds', 0):.0f}s |
            Output: {r.get('output_chars', 0):,} chars |
            Est. tokens: {r.get('estimated_tokens', 0):,}
        </div>
        {output_html}
        """

html += "</body></html>"

HTML(string=html).write_pdf('deep_research_output.pdf')
print('PDF saved: deep_research_output.pdf')
