"""Export the source-pinned design addendum; no network or application changes.

Run: python scripts/design/export_alignment.py
Requires scripts/tests/requirements-report.txt.
"""
from pathlib import Path
import html
import json
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/design/current"
DATA = json.loads((BASE / "alignment.json").read_text())
GREEN = colors.HexColor("#173f2f")
MUTED = colors.HexColor("#52665b")
PALE = colors.HexColor("#edf4ed")
WIDTH = A4[0] - 84

font_sets = [
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
fonts = next((pair for pair in font_sets if all(Path(p).is_file() for p in pair)), None)
if fonts is None:
    raise RuntimeError("Install Arial or DejaVu Sans to export this report")
for name, path in zip(("Design", "Design-Bold"), fonts):
    pdfmetrics.registerFont(TTFont(name, path))
pdfmetrics.registerFontFamily("Design", normal="Design", bold="Design-Bold", italic="Design", boldItalic="Design-Bold")
STYLES = {
    "title": ParagraphStyle("title", fontName="Design-Bold", fontSize=23, leading=28, textColor=GREEN, spaceAfter=15),
    "body": ParagraphStyle("body", fontName="Design", fontSize=9.3, leading=13.4, textColor=GREEN, spaceAfter=9),
    "small": ParagraphStyle("small", fontName="Design", fontSize=8, leading=11.1, textColor=MUTED, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="Design", fontSize=8.2, leading=11.3, textColor=GREEN),
    "head": ParagraphStyle("head", fontName="Design-Bold", fontSize=8.2, leading=11.3, textColor=GREEN),
}
DIAGRAMS = {
    "architecture": """flowchart TB
  UI["React client / same-origin Axios"]
  Host["FastAPI host + verified JWT"]
  Core["Core: accounts / preferences / fridge"]
  Recipes["Recipe generation + SqlRecipeStore"]
  Lists["CollectionsService + CoreCallbacks"]
  DB[("PostgreSQL / SQLAlchemy sessions")]
  CF["CloudflareRecipeProvider / Workers Free"]
  UI -->|HTTPS /api| Host
  Host --> Core
  Host --> Recipes
  Host --> Lists
  Core --> DB
  Recipes --> DB
  Lists --> DB
  Lists -.->|read-only inventory| Core
  Lists -.->|read-only owned recipe| Recipes
  Recipes -->|server-side HTTPS| CF
""",
    "generation": """sequenceDiagram
  participant UI as React client
  participant API as FastAPI + verified JWT
  participant Gen as RecipeGenerationService
  participant Store as SQL input / recipe store
  participant AI as CloudflareRecipeProvider
  UI->>API: POST /api/recipes/generate
  API->>Gen: generate(verified owner)
  Gen->>Store: Read fridge and preferences snapshot
  Store-->>Gen: GenerationInput; input session closed
  Gen->>AI: generate(input), max 28 seconds
  AI-->>Gen: Untrusted candidates
  Gen->>Gen: Validate complete batch and declared exclusions
  Gen->>Store: insert_batch(owner, recipes)
  Store-->>Gen: Transaction committed
  Gen-->>API: Persisted recipes
  API-->>UI: HTTP 200
  Note over Gen,Store: No inventory deduction
"""
}

def p(text, style="body"):
    escaped = html.escape(text)
    escaped = re.sub(r"([a-f0-9]{32})([a-f0-9]{8,32})", r"\1<wbr/>\2", escaped)
    return Paragraph(escaped, STYLES[style])

def arrow(drawing, x1, y1, x2, y2):
    drawing.add(Line(x1, y1, x2, y2, strokeColor=MUTED, strokeWidth=1))
    drawing.add(Polygon([x2, y2, x2-3, y2+6, x2+3, y2+6], fillColor=MUTED, strokeColor=MUTED))

def architecture():
    d = Drawing(WIDTH, 155)
    boxes = [
        (135, 125, 240, 27, ["React client / HTTPS /api"]),
        (135, 82, 240, 27, ["FastAPI host / verified JWT"]),
        (5, 38, 154, 27, ["Core / manual inventory"]),
        (178, 38, 154, 27, ["Recipe generation"]),
        (351, 38, 154, 27, ["Collections / owned reads"]),
        (20, 0, 285, 25, ["SQLAlchemy / PostgreSQL"]),
        (335, 0, 170, 25, ["Workers Free / HTTPS"]),
    ]
    for x, y, w, h, labels in boxes:
        d.add(Rect(x, y, w, h, rx=5, ry=5, strokeColor=colors.HexColor("#a3bba9"), fillColor=PALE))
        d.add(String(x+w/2, y+h/2-3, labels[0], textAnchor="middle", fontName="Design", fontSize=8, fillColor=GREEN))
    arrow(d, 255,125,255,109)
    for center in (82,255,428):
        d.add(Line(255,82,center,71,strokeColor=MUTED))
        arrow(d,center,71,center,65)
    for center in (82,255,428):
        d.add(Line(center,38,160,25,strokeColor=MUTED))
    d.add(Line(255,38,420,25,strokeColor=MUTED))
    return d

def generation():
    d=Drawing(WIDTH,72)
    labels=["Owned input","Provider","Validate","Commit","HTTP 200"]
    for i,label in enumerate(labels):
        x=i*103
        d.add(Rect(x,23,96,28,rx=4,ry=4,fillColor=PALE,strokeColor=colors.HexColor("#a3bba9")))
        d.add(String(x+48,34,label,textAnchor="middle",fontName="Design",fontSize=8,fillColor=GREEN))
        if i<4:d.add(Line(x+96,37,x+103,37,strokeColor=MUTED))
    d.add(String(0,5,"Snapshot closes before inference; inventory remains unchanged.",fontName="Design",fontSize=8,fillColor=MUTED))
    return d

def footer(c, doc):
    c.setStrokeColor(colors.HexColor("#d5e2d8"))
    c.line(42,38,A4[0]-42,38)
    c.setFont("Design",7)
    c.setFillColor(MUTED)
    c.drawString(42,26,"Fridgely | Design alignment | inspected source c671654 | 25 November 2026")
    c.drawRightString(A4[0]-42,26,str(doc.page))

story=[]
md=["# Fridgely design and implementation alignment","",
    "Inspected source: `"+DATA["source_sha"]+"`.",
    "Historical design: `"+DATA["historical_design_sha"]+"`.",""]
for index,page in enumerate(DATA["pages"]):
    if index:story.append(PageBreak())
    story.append(p(page["title"],"title"))
    md.extend(["## "+str(index+1)+". "+page["title"],""])
    if page.get("subtitle"):
        story.append(p(page["subtitle"],"small"));md.extend([page["subtitle"],""])
    for text in page.get("paragraphs",[]):
        story.append(p(text));md.extend([text,""])
    if page.get("diagram"):
        name=page["diagram"]
        story.extend([architecture() if name=="architecture" else generation(),Spacer(1,12)])
        md.extend(["```mermaid",DIAGRAMS[name].strip(),"```",""])
    rows=[page["headers"]]+page["rows"]
    table=Table([[p(value,"head" if i==0 else "cell") for value in row] for i,row in enumerate(rows)],
        colWidths=[155,WIDTH-155],repeatRows=1,hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PALE),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("LINEBELOW",(0,0),(-1,-1),0.3,colors.HexColor("#d5e2d8"))]))
    story.extend([table,Spacer(1,12)])
    md.append("| "+" | ".join(page["headers"])+" |")
    md.append("| --- | --- |")
    md.extend("| "+" | ".join(row)+" |" for row in page["rows"]);md.append("")
    for key in ("after","notes"):
        for text in page.get(key,[]):
            story.append(p(text,"small" if key=="notes" else "body"));md.extend([text,""])
    for label,url in page.get("links",[]):
        story.append(Paragraph('<a href="'+url+'" color="#256247"><u>'+html.escape(label)+'</u></a>',STYLES["small"]))
        md.extend(["["+label+"]("+url+")",""])
md.extend(["## Reproduction","",
    "From the repository root, install the existing `scripts/tests/requirements-report.txt` dependencies and run `python scripts/design/export_alignment.py`.",
    "The editable Mermaid diagrams accompany the simplified PDF diagrams. Both exports read `docs/design/current/alignment.json`.",
    "See `source-manifest.json` for the original model blob identities and the inspected application file identities. No model request is made during export.",""])
(BASE/"implementation-alignment.md").write_text("\n".join(md))
out=BASE/"implementation-alignment.pdf"
SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=53,
    title="Fridgely design and implementation alignment",author="Berfin Gökgöz",invariant=1).build(
    story,onFirstPage=footer,onLaterPages=footer,canvasmaker=canvas.Canvas)
print(out)
