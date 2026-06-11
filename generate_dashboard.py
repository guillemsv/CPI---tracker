"""
generate_dashboard.py — builds the GitHub Pages HTML dashboard
from output/cpi_latest.json and output/history.csv
"""

import json
import os
import pandas as pd
from datetime import datetime


def load_latest() -> dict:
    path = "output/cpi_latest.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def load_history() -> list:
    path = "output/history.csv"
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path).tail(90)  # last 90 days
    return df.fillna("null").to_dict(orient="records")


def build_html(data: dict, history: list) -> str:
    estimate = data.get("estimate", {})
    official = data.get("official", {})
    cats = data.get("category_breakdown", {})
    components = data.get("component_detail", [])
    timestamp = data.get("timestamp", "")[:10]

    headline = estimate.get("headline_cpi_pct", "N/A")
    core = estimate.get("core_cpi_pct", "N/A")
    coverage = estimate.get("basket_coverage_pct", 0)
    official_headline = official.get("headline_cpi_pct", "N/A")

    headline_str = f"{headline:+.2f}%" if isinstance(headline, (int, float)) else "N/A"
    core_str = f"{core:+.2f}%" if isinstance(core, (int, float)) else "N/A"
    official_str = f"{official_headline:+.2f}%" if isinstance(official_headline, (int, float)) else "N/A"

    # Build category rows
    cat_rows = ""
    for k, c in cats.items():
        yoy = c.get("avg_yoy_pct")
        contrib = c.get("contribution_bp", 0) or 0
        yoy_str = f"{yoy:+.1f}%" if yoy is not None else "–"
        bar_color = "#c0504d" if (yoy or 0) > 3 else ("#2d8653" if (yoy or 0) < 0 else "#2e75b6")
        bar_width = min(abs(contrib) / 2.5 * 100, 100)
        cat_rows += f"""
        <tr>
          <td>{c['label']}</td>
          <td style="text-align:center">{c['weight']:.1f}%</td>
          <td style="text-align:center;color:{bar_color};font-weight:600">{yoy_str}</td>
          <td style="text-align:center">{contrib:+.0f}bp</td>
          <td><div style="background:{bar_color};height:10px;width:{bar_width:.0f}%;border-radius:3px;min-width:2px"></div></td>
        </tr>"""

    # Build component rows (top 15 by weight)
    comp_rows = ""
    for c in sorted(components, key=lambda x: -x["weight"])[:15]:
        yoy = c.get("yoy_pct")
        yoy_str = f"{yoy:+.1f}%" if yoy is not None else "–"
        color = "#c0504d" if (yoy or 0) > 4 else ("#2d8653" if (yoy or 0) < 0 else "#404040")
        source_badge = f'<span style="font-size:10px;background:#e8f0f8;padding:1px 5px;border-radius:3px">{c.get("source","")}</span>'
        comp_rows += f"""
        <tr>
          <td style="padding-left:12px">{c['label']}</td>
          <td style="text-align:center">{c['weight']:.1f}%</td>
          <td style="text-align:center;color:{color};font-weight:600">{yoy_str}</td>
          <td>{source_badge}</td>
        </tr>"""

    # History chart data
    hist_labels = json.dumps([str(r.get("date", "")) for r in history])
    hist_est = json.dumps([r.get("headline_estimate") for r in history])
    hist_off = json.dumps([r.get("official_headline") for r in history])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>US CPI Tracker — Real-Time Inflation Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; background: #f4f6f9; color: #2c2c2c; font-size: 14px; }}
  .header {{ background: #1f4e79; color: white; padding: 20px 32px; }}
  .header h1 {{ font-size: 22px; font-weight: 600; }}
  .header p {{ font-size: 12px; opacity: 0.8; margin-top: 4px; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
  .card {{ background: white; border-radius: 8px; padding: 20px; border: 0.5px solid #e0e0e0; }}
  .metric-label {{ font-size: 11px; color: #808080; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
  .metric-value {{ font-size: 32px; font-weight: 600; color: #1f4e79; }}
  .metric-sub {{ font-size: 11px; color: #808080; margin-top: 4px; }}
  .metric-value.hot {{ color: #c0504d; }}
  .metric-value.cool {{ color: #2d8653; }}
  h2 {{ font-size: 14px; font-weight: 600; color: #1f4e79; margin-bottom: 12px; border-bottom: 1px solid #e8eef4; padding-bottom: 8px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #1f4e79; color: white; padding: 7px 10px; text-align: left; font-weight: 500; font-size: 11px; }}
  td {{ padding: 6px 10px; border-bottom: 0.5px solid #f0f0f0; }}
  tr:hover td {{ background: #f8fafc; }}
  .footer {{ text-align: center; font-size: 11px; color: #aaa; padding: 24px; }}
  .badge-coverage {{ display: inline-block; background: #e8f4ec; color: #2d8653; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
  @media (max-width: 600px) {{ .grid-3, .grid-2 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>

<div class="header">
  <h1>📊 US CPI Tracker — Real-Time Inflation Monitor</h1>
  <p>Daily-updated CPI nowcast built from EIA, FRED, Zillow, BLS APIs &nbsp;|&nbsp; Updated: {timestamp} &nbsp;|&nbsp;
     <span class="badge-coverage" style="background:rgba(255,255,255,0.15);color:white">{coverage}% basket covered</span></p>
</div>

<div class="container">

  <!-- Summary cards -->
  <div class="grid-3">
    <div class="card">
      <div class="metric-label">Our Headline CPI Estimate</div>
      <div class="metric-value {'hot' if isinstance(headline,(int,float)) and headline > 3 else 'cool' if isinstance(headline,(int,float)) and headline < 2 else ''}">{headline_str}</div>
      <div class="metric-sub">YoY % | Weighted avg of scraped data</div>
    </div>
    <div class="card">
      <div class="metric-label">Our Core CPI Estimate</div>
      <div class="metric-value {'hot' if isinstance(core,(int,float)) and core > 3 else ''}">{core_str}</div>
      <div class="metric-sub">YoY % | Ex-food & energy</div>
    </div>
    <div class="card">
      <div class="metric-label">BLS Official (latest release)</div>
      <div class="metric-value">{official_str}</div>
      <div class="metric-sub">Released {official.get('date','')} | Lags ~2 weeks</div>
    </div>
  </div>

  <!-- Chart + category table -->
  <div class="grid-2">
    <div class="card">
      <h2>Historical Estimate vs BLS Official</h2>
      <canvas id="histChart" style="max-height:280px"></canvas>
    </div>
    <div class="card">
      <h2>Category Breakdown</h2>
      <table>
        <thead><tr><th>Category</th><th>Weight</th><th>YoY %</th><th>Contrib.</th><th>Magnitude</th></tr></thead>
        <tbody>{cat_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Component detail -->
  <div class="card">
    <h2>Component Detail (top 15 by weight)</h2>
    <table>
      <thead><tr><th>Component</th><th>CPI Weight</th><th>YoY %</th><th>Source</th></tr></thead>
      <tbody>{comp_rows}</tbody>
    </table>
  </div>

  <!-- Methodology note -->
  <div class="card" style="margin-top:20px;font-size:12px;color:#666;line-height:1.7">
    <h2>Methodology</h2>
    <strong>What this is:</strong> A CPI nowcast that replicates ~{coverage}% of the BLS CPI-U basket using real-time data from public APIs
    (EIA for energy, FRED/BLS for rents & vehicles, Zillow for leading OER signal). Remaining components use recent historical averages as fallback.<br><br>
    <strong>Key caveat:</strong> OER (24% of CPI) has a 12-15 month lag vs market rents — our estimate uses the BLS OER series directly,
    which means housing inflation is already "baked in" for the next 12 months regardless of where market rents go today.<br><br>
    <strong>Data sources:</strong> EIA Open Data API &nbsp;|&nbsp; FRED API (St. Louis Fed) &nbsp;|&nbsp; Zillow Research CSV &nbsp;|&nbsp; BLS Public API<br>
    <strong>Update frequency:</strong> Daily at 08:00 UTC via GitHub Actions
  </div>

</div>

<div class="footer">
  Built with Python + GitHub Actions + GitHub Pages &nbsp;|&nbsp; Data: EIA, FRED, Zillow, BLS &nbsp;|&nbsp; Not investment advice
</div>

<script>
const labels = {hist_labels};
const estData = {hist_est};
const offData = {hist_off};

new Chart(document.getElementById('histChart'), {{
  type: 'line',
  data: {{
    labels: labels,
    datasets: [
      {{
        label: 'Our Estimate',
        data: estData,
        borderColor: '#2e75b6',
        backgroundColor: 'rgba(46,117,182,0.08)',
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.3,
        fill: true,
      }},
      {{
        label: 'BLS Official',
        data: offData,
        borderColor: '#c0504d',
        borderWidth: 2,
        borderDash: [5,3],
        pointRadius: 3,
        tension: 0.3,
      }},
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, boxWidth: 12 }} }},
      tooltip: {{ mode: 'index', intersect: false }}
    }},
    scales: {{
      y: {{ title: {{ display: true, text: 'YoY %', font: {{ size: 11 }} }}, ticks: {{ font: {{ size: 10 }} }} }},
      x: {{ ticks: {{ font: {{ size: 10 }}, maxTicksLimit: 8 }} }}
    }}
  }}
}});
</script>
</body>
</html>"""


def main():
    data = load_latest()
    history = load_history()
    html = build_html(data, history)
    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/index.html", "w") as f:
        f.write(html)
    print("✓ Dashboard generated at dashboard/index.html")


if __name__ == "__main__":
    main()
