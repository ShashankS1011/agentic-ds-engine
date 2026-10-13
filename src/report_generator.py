import datetime
from html import escape

def generate_html_report(query_text: str, sql_query: str, query_result: str, summary_text: str, plotly_fig=None) -> str:
    """Bundles analysis artifacts into a self-contained HTML executive report."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    
    chart_html = ""
    if plotly_fig is not None:
        chart_html = f"""
        <div class="card">
            <h2>Data Visualization</h2>
            {plotly_fig.to_html(full_html=False, include_plotlyjs="cdn")}
        </div>
        """
        
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Executive Data Analysis Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 40px; background-color: #f9f9fb; color: #1a1a1a; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .card {{ background: #ffffff; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e5e5e5; }}
            h1 {{ margin-top: 0; color: #111; border-bottom: 2px solid #eee; padding-bottom: 12px; }}
            h2 {{ color: #333; font-size: 1.25rem; margin-top: 0; }}
            .meta {{ color: #666; font-size: 0.875rem; margin-bottom: 20px; }}
            pre {{ background: #282c34; color: #abb2bf; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 0.9rem; }}
            .summary {{ background: #f0f7ff; border-left: 4px solid #0066cc; padding: 16px; border-radius: 4px; font-size: 1.05rem; line-height: 1.6; }}
            table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Executive Data Analysis Report</h1>
            <div class="meta">Generated on: {timestamp}</div>
            
            <div class="card">
                <h2>User Query</h2>
                <p><strong>"{escape(query_text)}"</strong></p>
            </div>
            
            <div class="card">
                <h2>Executive Summary</h2>
                <div class="summary">{escape(summary_text)}</div>
            </div>
            
            {chart_html}
            
            <div class="card">
                <h2>Generated SQL Query</h2>
                <pre><code>{escape(sql_query)}</code></pre>
            </div>
            
            <div class="card">
                <h2>Raw Execution Result</h2>
                <pre>{escape(query_result)}</pre>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content