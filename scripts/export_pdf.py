"""Render the Markdown requirements report and embed all local diagram images.

Usage: python scripts/export_pdf.py --output path/to/report.pdf
Dependencies: reportlab, Pillow. Run from the repository or any directory.
Optional --font-dir selects a directory with arial.ttf and arialbd.ttf.
Default fonts: Windows Arial; otherwise reportlab's bundled Vera fonts.
"""
from pathlib import Path
from datetime import date
import argparse, re, html
from urllib.parse import urljoin
from PIL import Image as PILImage, ImageDraw, ImageFont
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT/'docs/plans/images'
BASE = 'https://github.com/SarpCizer/CMPE331-Project/blob/requirements_work/docs/'


def fonts(font_dir=None):
    directory = Path(font_dir or 'C:/Windows/Fonts')
    regular,bold = directory/'arial.ttf',directory/'arialbd.ttf'
    if not regular.exists():
        directory = Path(reportlab.__file__).parent/'fonts'
        regular,bold = directory/'Vera.ttf',directory/'VeraBd.ttf'
    pdfmetrics.registerFont(TTFont('Body',str(regular)))
    pdfmetrics.registerFont(TTFont('BodyBold',str(bold)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
    return str(regular),str(bold)

def diagrams(font_regular,font_bold):
    IMAGES.mkdir(parents=True,exist_ok=True)
    navy='#19354D'; grey='#E9EFF4'; ink='#17202A'; line='#718496'
    def canvas(w,h):
        im = PILImage.new('RGB',(w,h),'white'); return im,ImageDraw.Draw(im)
    def text(draw,xy,t,size=27,bold=False,fill=ink):
        draw.text(xy,t,font=ImageFont.truetype(font_bold if bold else font_regular,size),fill=fill)
    def centered(draw,xy,t,size=27,bold=False,fill=ink):
        draw.text(xy,t,font=ImageFont.truetype(font_bold if bold else font_regular,size),fill=fill,anchor='mm')
    im,d=canvas(1900,760)
    centered(d,(950,65),'Fridgely work breakdown structure',44,True)
    d.rounded_rectangle((780,115,1120,195),radius=10,fill=navy)
    centered(d,(950,155),'Fridgely',34,True,'white')
    groups=[('1 Requirements',['1.1 Plan and stories','1.2 Tests and report','1.3 Review and PDF']),
            ('2 Analysis',['2.1 Domain and ER','2.2 Flows and report']),
            ('3 Design and build',['3.1 Architecture','3.2 Accounts','3.3 Fridge','3.4 Recipes','3.5 Shopping and saved','3.6 Responsive UI','3.7 Design report']),
            ('4 Quality',['4.1 TDD and CI','4.2 Testing report']),
            ('5 Release',['5.1 Deploy and code','5.2 Presentation'])]
    for i,(label,items) in enumerate(groups):
        left=30+i*375; cx=left+170
        d.line((950,195,950,230,cx,230,cx,270),fill=line,width=4)
        d.rounded_rectangle((left,270,left+340,345),radius=8,fill=navy)
        centered(d,(cx,308),label,28,True,'white')
        d.rounded_rectangle((left,365,left+340,700),radius=8,fill=grey,outline=line,width=2)
        for j,item in enumerate(items): text(d,(left+18,385+j*42),item,25)
    centered(d,(950,735),'Owners, work windows and exit artifacts are specified in wbs.md',25)
    im.save(IMAGES/'wbs.png')

    from requirements_diagrams import render
    render(font_regular,font_bold)


def inline(raw):
    raw=raw.replace('≤','<=')
    chunks=[]; pos=0
    pattern=re.compile(r'\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`|\*\*([^*]+)\*\*')
    for m in pattern.finditer(raw):
        chunks.append(html.escape(raw[pos:m.start()]))
        if m.group(1):
            url=m.group(2)
            if not url.startswith(('https://','http://')): url=urljoin(BASE,url)
            chunks.append(f'<a href="{html.escape(url,quote=True)}" color="#244C70">{html.escape(m.group(1))}</a>')
        elif m.group(3): chunks.append('<font name="Body">'+html.escape(m.group(3))+'</font>')
        else: chunks.append('<b>'+html.escape(m.group(4))+'</b>')
        pos=m.end()
    chunks.append(html.escape(raw[pos:]))
    return ''.join(chunks)

def export(output,font_dir=None):
    regular,bold=fonts(font_dir); diagrams(regular,bold)
    styles={
        'body':ParagraphStyle('body',fontName='Body',fontSize=9.8,leading=14.3,spaceAfter=8),
        'title':ParagraphStyle('title',fontName='BodyBold',fontSize=23,leading=28,spaceAfter=14,keepWithNext=True),
        'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=15,leading=20,spaceBefore=16,spaceAfter=8,keepWithNext=True),
        'h3':ParagraphStyle('h3',fontName='BodyBold',fontSize=11.8,leading=16,spaceBefore=11,spaceAfter=6,keepWithNext=True),
        'list':ParagraphStyle('list',fontName='Body',fontSize=9.8,leading=14.3,leftIndent=12,firstLineIndent=-12,spaceAfter=5),
        'cell':ParagraphStyle('cell',fontName='Body',fontSize=9,leading=12),
        'header':ParagraphStyle('header',fontName='BodyBold',fontSize=9,leading=12,textColor=colors.white),
        'caption':ParagraphStyle('caption',fontName='Body',fontSize=9,leading=12,textColor=colors.HexColor('#44515D'),spaceAfter=12),
    }
    story=[]
    width=A4[0]-100
    lines=(ROOT/'docs/requirements-specification.md').read_text(encoding='utf-8').splitlines()
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('!['):
            m=re.match(r'!\[([^\]]+)\]\(([^)]+)\)',line)
            imgpath=ROOT/'docs'/m.group(2)
            with PILImage.open(imgpath) as pic: w,h=pic.size
            story.append(KeepTogether([Image(str(imgpath),width=width,height=width*h/w),Spacer(1,5),Paragraph(inline(m.group(1)),styles['caption'])]))
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*',c) for c in row): rows.append([c.strip() for c in row])
                i+=1
            cells=[[Paragraph(inline(c),styles['header'] if r==0 else styles['cell']) for c in row] for r,row in enumerate(rows)]
            table=Table(cells,colWidths=([width*.20,width*.80] if len(rows[0])==2 else [width/len(rows[0])]*len(rows[0])),repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#19354D')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F4F7')]),
                ('GRID',(0,0),(-1,-1),.5,colors.HexColor('#D9D9D9')),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
                ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ]))
            story.extend([table,Spacer(1,10)]); continue
        elif line.startswith('# '): story.append(Paragraph(inline(line[2:]),styles['title']))
        elif line.startswith('## '): story.append(Paragraph(inline(line[3:]),styles['h2']))
        elif line.startswith('### '): story.append(Paragraph(inline(line[4:]),styles['h3']))
        elif re.match(r'^\d+\. ',line) or line.startswith('- '): story.append(Paragraph(inline(line),styles['list']))
        else:
            text=line
            while i+1<len(lines) and lines[i+1].strip() and not re.match(r'^(#|!\[|\||\d+\. |-[ ])',lines[i+1].strip()):
                i+=1; text+=' '+lines[i].strip()
            story.append(Paragraph(inline(text),styles['body']))
        i+=1
    # Keep each short requirement together so its owner/criteria do not spill
    # away from its heading and user-story statement.
    grouped=[]; i=0
    while i<len(story):
        item=story[i]
        if isinstance(item,Paragraph) and item.style.name=='h3':
            block=[item]; i+=1
            while i<len(story) and not (isinstance(story[i],Paragraph) and story[i].style.name in ('h2','h3')):
                block.append(story[i]); i+=1
            grouped.append(KeepTogether(block))
        else:
            grouped.append(item); i+=1
    story=grouped
    def footer(c,doc):
        c.saveState(); c.setFont('Body',8); c.setFillColor(colors.HexColor('#56616C'))
        c.drawString(50,25,'Fridgely requirements | Review copy | Revised 11 October 2026')
        c.drawRightString(A4[0]-50,25,str(doc.page)); c.restoreState()
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=42,bottomMargin=44,
        title='Fridgely requirements specification',author='Fridgely project team')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print('Rendered',output)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--font-dir')
    args=p.parse_args(); export(args.output,args.font_dir)
