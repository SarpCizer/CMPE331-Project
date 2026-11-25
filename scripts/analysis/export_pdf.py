"""Export the complete analysis Markdown report with separate readable figures.

Requirements: reportlab and Pillow. SVGs use matching pre-rendered PNGs from
--diagram-dir, rather than a remote renderer. Source files are never modified.
Example (from any directory):
    python scripts/analysis/export_pdf.py --diagram-dir /tmp/analysis-pages \
        --output /tmp/Fridgely_Analysis_Review.pdf
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit

from PIL import Image as PillowImage
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, LongTable, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, TableStyle, XPreformatted,
)


ROOT = Path(__file__).resolve().parents[2]
INK = colors.HexColor('#183849')
MUTED = colors.HexColor('#536572')
LINK = '#176081'
RULE = colors.HexColor('#CBD8DF')
PORTRAIT = A4
DIAGRAM = landscape(A3)
OVERVIEW_PAPERS = {'A1': landscape(A1), 'A2': landscape(A2), 'A3': DIAGRAM}
TEXT_MARGIN = 45
FIGURE_MARGIN = 38
TOP = 49
BOTTOM = 46


def normalized(text: str) -> str:
    """Keep typography predictable in both Windows and portable font fallbacks."""
    return (text.replace('\u2011', '-').replace('\u2013', '-')
            .replace('\u2014', ' - ').replace('\u2212', '-'))


def register_fonts(font_dir: Path | None) -> None:
    directory = font_dir or Path('C:/Windows/Fonts')
    if (directory / 'arial.ttf').is_file():
        paths = {
            'AnalysisBody': directory / 'arial.ttf',
            'AnalysisBold': directory / 'arialbd.ttf',
            'AnalysisItalic': directory / 'ariali.ttf',
            'AnalysisBoldItalic': directory / 'arialbi.ttf',
        }
        mono = directory / 'consola.ttf'
    else:
        directory = Path(reportlab.__file__).parent / 'fonts'
        paths = {
            'AnalysisBody': directory / 'Vera.ttf',
            'AnalysisBold': directory / 'VeraBd.ttf',
            'AnalysisItalic': directory / 'VeraIt.ttf',
            'AnalysisBoldItalic': directory / 'VeraBI.ttf',
        }
        mono = directory / 'Vera.ttf'
    for name, path in paths.items():
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFont(TTFont('AnalysisMono', str(mono if mono.exists() else paths['AnalysisBody'])))
    pdfmetrics.registerFontFamily(
        'AnalysisBody', normal='AnalysisBody', bold='AnalysisBold',
        italic='AnalysisItalic', boldItalic='AnalysisBoldItalic',
    )


class MarkdownInline:
    """Small inline renderer with balanced link destinations and escaped XML."""

    def __init__(self, source: Path, branch: str):
        self.source = source
        self.branch = branch
        self.links: set[str] = set()

    def url(self, target: str) -> str:
        target = target.strip().removeprefix('<').removesuffix('>')
        parts = urlsplit(target)
        if parts.scheme:
            if parts.scheme.lower() not in {'http', 'https', 'mailto'}:
                raise ValueError(f'Unsupported link scheme in {target!r}')
            result = target
        else:
            origin = self.source.relative_to(ROOT).as_posix()
            relative = unquote(parts.path)
            combined = posixpath.normpath(posixpath.join(posixpath.dirname(origin), relative)) if relative else origin
            if combined.startswith('../') or combined.startswith('/'):
                raise ValueError(f'Link escapes the repository: {target!r}')
            result = (
                'https://github.com/SarpCizer/CMPE331-Project/blob/'
                + quote(self.branch, safe='') + '/' + quote(combined, safe='/')
            )
            if parts.query:
                result += '?' + parts.query
            if parts.fragment:
                result += '#' + quote(unquote(parts.fragment), safe='-_.~')
        self.links.add(result)
        return result

    @staticmethod
    def link_at(text: str, start: int):
        """Return label/destination/end for a Markdown link starting at '['."""
        end_label = text.find('](', start + 1)
        if end_label == -1:
            return None
        depth, j = 1, end_label + 2
        begin = j
        while j < len(text):
            if text[j] == '\\':
                j += 2
                continue
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
                if depth == 0:
                    destination = text[begin:j].strip()
                    # Optional quoted Markdown title is not part of the URL.
                    destination = re.sub(r'\s+[\"\'][^\"\']*[\"\']$', '', destination)
                    return text[start + 1:end_label], destination, j + 1
            j += 1
        return None

    def render(self, raw: str) -> str:
        text = normalized(raw)
        out, i = [], 0
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in r'\\`*_{}[]()#+-.!|':
                out.append(html.escape(text[i + 1]))
                i += 2
                continue
            if text.startswith('<br>', i) or text.startswith('<br/>', i) or text.startswith('<br />', i):
                end = text.index('>', i)
                out.append('<br/>')
                i = end + 1
                continue
            if text[i] == '`':
                stop = text.find('`', i + 1)
                if stop != -1:
                    out.append('<font name="AnalysisMono" size="8.5">' + html.escape(text[i + 1:stop]) + '</font>')
                    i = stop + 1
                    continue
            if text[i] == '[':
                link = self.link_at(text, i)
                if link:
                    label, destination, end = link
                    url = self.url(destination)
                    out.append(f'<a href="{html.escape(url, quote=True)}" color="{LINK}">{self.render(label)}</a>')
                    i = end
                    continue
            if text[i] == '<':
                stop = text.find('>', i + 1)
                if stop != -1 and text[i + 1:stop].startswith(('https://', 'http://', 'mailto:')):
                    url = self.url(text[i + 1:stop])
                    out.append(f'<a href="{html.escape(url, quote=True)}" color="{LINK}">{html.escape(text[i + 1:stop])}</a>')
                    i = stop + 1
                    continue
            marker = '**' if text.startswith('**', i) else ('*' if text[i] == '*' else None)
            if marker:
                stop = text.find(marker, i + len(marker))
                if stop != -1:
                    tag = 'b' if marker == '**' else 'i'
                    out.append(f'<{tag}>' + self.render(text[i + len(marker):stop]) + f'</{tag}>')
                    i = stop + len(marker)
                    continue
            out.append(html.escape(text[i]))
            i += 1
        return ''.join(out)


@dataclass
class Block:
    kind: str
    value: object
    level: int = 0


IMAGE = re.compile(r'^!\[([^\]]*)\]\((.+)\)\s*$')
HEADING = re.compile(r'^(#{1,6})\s+(.+?)\s*#*\s*$')
LIST = re.compile(r'^(\s*)([-+*]|\d+[.)])\s+(.+)$')


def table_cells(line: str) -> list[str]:
    line = line.strip().strip('|')
    cells, current, escaped, code = [], [], False, False
    for character in line:
        if escaped:
            current.extend(('\\', character))
            escaped = False
        elif character == '\\':
            escaped = True
        elif character == '`':
            code = not code
            current.append(character)
        elif character == '|' and not code:
            cells.append(''.join(current).strip())
            current = []
        else:
            current.append(character)
    if escaped:
        current.append('\\')
    cells.append(''.join(current).strip())
    return cells


def parse_markdown(text: str) -> list[Block]:
    """Retain report prose, headings, lists, tables, code and every local image."""
    lines = text.splitlines()
    blocks, i = [], 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue
        image = IMAGE.fullmatch(line)
        heading = HEADING.fullmatch(line)
        item = LIST.match(raw)
        if image:
            blocks.append(Block('image', image.groups()))
            i += 1
        elif heading:
            blocks.append(Block('heading', heading.group(2), len(heading.group(1))))
            i += 1
        elif line.startswith(('```', '~~~')):
            fence = line[:3]
            language = line[3:].strip()
            content = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                content.append(lines[i])
                i += 1
            if i == len(lines):
                raise ValueError('Unclosed Markdown code fence')
            i += 1
            # Omit a diagram source only when its rendered image is adjacent.
            neighbors = lines[max(0, i - len(content) - 5):max(0, i - len(content) - 2)] + lines[i:i + 3]
            paired_image = any(IMAGE.fullmatch(candidate.strip()) for candidate in neighbors)
            if language.lower() != 'mermaid' or not paired_image:
                blocks.append(Block('code', '\n'.join(content)))
        elif line.startswith('|') and i + 1 < len(lines) and all(re.fullmatch(r':?-{3,}:?', c.replace(' ', '')) for c in table_cells(lines[i + 1])):
            rows = [table_cells(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(table_cells(lines[i]))
                i += 1
            expected = len(rows[0])
            if any(len(row) != expected for row in rows):
                raise ValueError('Inconsistent column count in Markdown table')
            blocks.append(Block('table', rows))
        elif item:
            indentation, marker, content = item.groups()
            i += 1
            continuation = []
            while i < len(lines) and lines[i].strip() and lines[i].startswith(' ' * (len(indentation) + 2)) and not LIST.match(lines[i]) and not IMAGE.fullmatch(lines[i].strip()):
                continuation.append(lines[i].strip())
                i += 1
            blocks.append(Block('list', (marker, ' '.join([content] + continuation)), len(indentation) // 2))
        elif re.fullmatch(r'([-*_])(?:\s*\1){2,}', line):
            blocks.append(Block('rule', ''))
            i += 1
        else:
            paragraph = [line]
            i += 1
            while i < len(lines) and lines[i].strip():
                candidate = lines[i]
                if HEADING.fullmatch(candidate.strip()) or IMAGE.fullmatch(candidate.strip()) or LIST.match(candidate) or candidate.strip().startswith(('|', '```', '~~~')):
                    break
                paragraph.append(candidate.strip())
                i += 1
            if all(part.startswith('>') for part in paragraph):
                blocks.append(Block('quote', ' '.join(part.lstrip('>').strip() for part in paragraph)))
            else:
                blocks.append(Block('paragraph', ' '.join(paragraph)))
    return blocks


def styles() -> dict[str, ParagraphStyle]:
    body = dict(fontName='AnalysisBody', textColor=INK, fontSize=10, leading=14.5, spaceAfter=8)
    result = {
        'body': ParagraphStyle('AnalysisBodyStyle', **body),
        'quote': ParagraphStyle('AnalysisQuoteStyle', leftIndent=16, rightIndent=8, **body),
        'title': ParagraphStyle('AnalysisTitle', fontName='AnalysisBold', textColor=INK, fontSize=23, leading=28, spaceAfter=15, keepWithNext=True),
        'h2': ParagraphStyle('AnalysisH2', fontName='AnalysisBold', textColor=INK, fontSize=15, leading=20, spaceBefore=15, spaceAfter=8, keepWithNext=True),
        'h3': ParagraphStyle('AnalysisH3', fontName='AnalysisBold', textColor=INK, fontSize=12, leading=16, spaceBefore=10, spaceAfter=6, keepWithNext=True),
        'h4': ParagraphStyle('AnalysisH4', fontName='AnalysisBold', textColor=INK, fontSize=10.5, leading=14.5, spaceBefore=8, spaceAfter=5, keepWithNext=True),
        'cell': ParagraphStyle('AnalysisCell', fontName='AnalysisBody', textColor=INK, fontSize=8.5, leading=11.4, spaceAfter=0),
        'cell_header': ParagraphStyle('AnalysisCellHeader', fontName='AnalysisBold', textColor=colors.white, fontSize=8.5, leading=11.4, spaceAfter=0),
        'figure_heading': ParagraphStyle('AnalysisFigureHeading', fontName='AnalysisBold', textColor=INK, fontSize=16, leading=21, spaceAfter=7),
        'caption': ParagraphStyle('AnalysisCaption', fontName='AnalysisBody', textColor=MUTED, fontSize=9, leading=12, spaceAfter=4),
        'code': ParagraphStyle('AnalysisCode', fontName='AnalysisMono', textColor=INK, fontSize=8, leading=10.5, spaceAfter=9, borderPadding=6, backColor=colors.HexColor('#F0F5F7')),
    }
    return result


class NumberedCanvas(canvas.Canvas):
    """Replay page states so mixed-size pages receive correct total page labels."""

    def __init__(self, *args, review_label: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_states = []
        self.review_label = review_label

    def showPage(self):
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        count = len(self._page_states)
        for state in self._page_states:
            self.__dict__.update(state)
            width, _ = self._pagesize
            margin = FIGURE_MARGIN if width > PORTRAIT[0] + 1 else TEXT_MARGIN
            self.setStrokeColor(RULE)
            self.setLineWidth(0.5)
            self.line(margin, 35, width - margin, 35)
            self.setFont('AnalysisBody', 8)
            self.setFillColor(MUTED)
            self.drawString(margin, 22, normalized(self.review_label))
            self.drawRightString(width - margin, 22, f'Page {self._pageNumber} of {count}')
            super().showPage()
        super().save()


def page_header(pdf_canvas, document):
    width, height = pdf_canvas._pagesize
    margin = FIGURE_MARGIN if width > PORTRAIT[0] + 1 else TEXT_MARGIN
    pdf_canvas.saveState()
    pdf_canvas.setFillColor(MUTED)
    pdf_canvas.setFont('AnalysisBody', 8)
    pdf_canvas.drawString(margin, height - 23, 'FRIDGELY  /  CMPE 331  /  REQUIREMENTS ANALYSIS')
    pdf_canvas.setStrokeColor(RULE)
    pdf_canvas.setLineWidth(0.5)
    pdf_canvas.line(margin, height - 31, width - margin, height - 31)
    pdf_canvas.restoreState()


def make_table(rows: list[list[str]], inline: MarkdownInline, sheet_width: float, style: dict):
    columns = len(rows[0])
    # Estimate sensible widths from content, while guaranteeing room to wrap.
    weights = []
    for column in range(columns):
        lengths = [len(re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', row[column])) for row in rows]
        weights.append(max(10, min(48, max(lengths) ** 0.75 * 2)))
    widths = [sheet_width * weight / sum(weights) for weight in weights]
    data = [[Paragraph(inline.render(cell), style['cell_header' if r == 0 else 'cell']) for cell in row] for r, row in enumerate(rows)]
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign='LEFT', splitInRow=1, spaceBefore=3, spaceAfter=11)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EEF4F6')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, INK),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, RULE),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def local_image(target: str, source: Path, diagram_dir: Path | None) -> tuple[Path, Path]:
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        raise ValueError(f'Only local report images are supported: {target}')
    original = (source.parent / unquote(parts.path)).resolve()
    if not original.is_relative_to(ROOT):
        raise ValueError(f'Image escapes the repository: {target}')
    if not original.is_file():
        raise FileNotFoundError(f'Report image does not exist: {original}')
    if original.suffix.lower() == '.svg':
        if diagram_dir is None:
            raise ValueError(f'SVG {original.name} requires --diagram-dir with a matching PNG')
        rendered = diagram_dir / (original.stem + '.png')
        if not rendered.is_file():
            raise FileNotFoundError(f'Pre-rendered diagram is missing: {rendered}')
        return original, rendered
    return original, original


def export(source: Path, output: Path, diagram_dir: Path | None, branch: str, review_date: str, font_dir: Path | None, overview_paper: str = 'A1'):
    source, output = source.resolve(), output.resolve()
    if not source.is_relative_to(ROOT):
        raise ValueError('The input report must be within the repository for correct source links')
    register_fonts(font_dir)
    inline = MarkdownInline(source, branch)
    style = styles()
    blocks = parse_markdown(source.read_text(encoding='utf-8'))
    story, figures = [], []
    template = 'Portrait'
    first_template = 'Portrait'
    text_width = PORTRAIT[0] - 2 * TEXT_MARGIN
    overview_size = OVERVIEW_PAPERS[overview_paper]
    pending_heading = None

    def switch(next_template: str):
        nonlocal template, first_template
        if story:
            story.extend((NextPageTemplate(next_template), PageBreak()))
        else:
            first_template = next_template
        template = next_template

    for index, block in enumerate(blocks):
        if block.kind == 'heading' and index + 1 < len(blocks) and blocks[index + 1].kind == 'image':
            # Section titles immediately above a figure travel onto that sheet.
            pending_heading = block
            continue
        if block.kind == 'image':
            label, target = block.value
            original, rendered = local_image(target, source, diagram_dir)
            # The complete level-1 DFD is an intentionally dense overview. A1
            # keeps its 16px source labels readable at roughly 11pt; individual
            # story DFDs and data diagrams retain the regular A3 figure sheets.
            overview = original.name == 'level-1-dfd.svg'
            sheet = overview_size if overview else DIAGRAM
            figure_width = sheet[0] - 2 * FIGURE_MARGIN
            figure_height = sheet[1] - TOP - BOTTOM
            switch('Overview' if overview else 'Diagram')
            figure_number = len(figures) + 1
            figure_title = f'Figure {figure_number:02d}. ' + (label or original.stem)
            section_height = 0
            if pending_heading is not None:
                source_heading = str(pending_heading.value)
                if re.match(r'^Figure\s+\d+\s*[:.]\s*', source_heading, flags=re.IGNORECASE):
                    figure_title = f'Figure {figure_number:02d}. ' + re.sub(r'^Figure\s+\d+\s*[:.]\s*', '', source_heading, flags=re.IGNORECASE)
                else:
                    section = Paragraph(inline.render(source_heading), style['figure_heading'])
                    story.append(section)
                    _, section_height = section.wrap(figure_width, figure_height)
                pending_heading = None
            heading = Paragraph(inline.render(figure_title), style['figure_heading'])
            _, heading_height = heading.wrap(figure_width, figure_height)
            caption = Paragraph(
                'Source: ' + inline.render(f'[{original.relative_to(ROOT).as_posix()}]({target})'),
                style['caption'],
            )
            _, caption_height = caption.wrap(figure_width, figure_height)
            with PillowImage.open(rendered) as picture:
                image_width, image_height = picture.size
                picture.verify()
            available_height = figure_height - section_height - heading_height - caption_height - 37
            if available_height < 100:
                raise ValueError(f'Caption leaves insufficient room for figure: {original.name}')
            scale = min(figure_width / image_width, available_height / image_height)
            image = Image(str(rendered), width=image_width * scale, height=image_height * scale, hAlign='LEFT')
            story.extend((heading, Spacer(1, 5), image, Spacer(1, 8), caption))
            figures.append({
                'number': figure_number,
                'label': label,
                'source': original.relative_to(ROOT).as_posix(),
                'rendered': str(rendered),
                'width_pt': round(image.drawWidth, 2),
                'height_pt': round(image.drawHeight, 2),
                'paper': f'{overview_paper if overview else "A3"} landscape',
                'page_width_pt': round(sheet[0], 2),
                'page_height_pt': round(sheet[1], 2),
            })
            continue
        if template in {'Diagram', 'Overview'}:
            switch('Portrait')
        if block.kind == 'heading':
            name = 'title' if block.level == 1 else 'h2' if block.level == 2 else 'h3' if block.level == 3 else 'h4'
            story.append(Paragraph(inline.render(str(block.value)), style[name]))
        elif block.kind in {'paragraph', 'quote'}:
            paragraph_style = style['quote' if block.kind == 'quote' else 'body']
            visible_text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', str(block.value))
            if block.kind == 'paragraph' and len(visible_text) <= 240 and index + 1 < len(blocks) and blocks[index + 1].kind == 'list':
                # Keep short source introductions with the first substantive
                # bullet; the preceding section heading already stays with it.
                paragraph_style = ParagraphStyle(f'AnalysisListIntro{index}', parent=paragraph_style, keepWithNext=True)
            story.append(Paragraph(inline.render(str(block.value)), paragraph_style))
        elif block.kind == 'list':
            marker, content = block.value
            indentation = 13 + min(block.level, 5) * 13
            item_style = ParagraphStyle(
                f'AnalysisList{index}', parent=style['body'], leftIndent=indentation,
                firstLineIndent=-11, spaceAfter=5,
            )
            marker = '-' if marker in {'-', '+', '*'} else marker
            story.append(Paragraph(html.escape(marker) + ' ' + inline.render(content), item_style))
        elif block.kind == 'table':
            story.append(make_table(block.value, inline, text_width - 12, style))
        elif block.kind == 'code':
            story.append(XPreformatted(html.escape(normalized(str(block.value))), style['code'], maxLineLength=94))
        elif block.kind == 'rule':
            story.append(HRFlowable(width='100%', thickness=0.5, color=RULE, spaceBefore=5, spaceAfter=9))
        else:
            raise ValueError(f'Unsupported Markdown block: {block.kind}')

    if not story:
        raise ValueError('The Markdown report is empty')
    output.parent.mkdir(parents=True, exist_ok=True)
    review_label = f'Revised {review_date} | Review copy'
    document = BaseDocTemplate(
        str(output), pagesize=PORTRAIT, leftMargin=TEXT_MARGIN,
        rightMargin=TEXT_MARGIN, topMargin=TOP, bottomMargin=BOTTOM,
        title='Fridgely requirements analysis report',
        author='Fridgely project team - CMPE 331',
        subject=review_label, pageCompression=1,
        allowSplitting=1,
    )
    templates = [
        PageTemplate(
            id='Portrait', pagesize=PORTRAIT, onPage=page_header,
            frames=[Frame(TEXT_MARGIN, BOTTOM, text_width, PORTRAIT[1] - TOP - BOTTOM, id='Text', leftPadding=6, rightPadding=6, topPadding=0, bottomPadding=0)],
        ),
        PageTemplate(
            id='Diagram', pagesize=DIAGRAM, onPage=page_header,
            frames=[Frame(FIGURE_MARGIN, BOTTOM, DIAGRAM[0] - 2 * FIGURE_MARGIN, DIAGRAM[1] - TOP - BOTTOM, id='Figure', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
        ),
        PageTemplate(
            id='Overview', pagesize=overview_size, onPage=page_header,
            frames=[Frame(FIGURE_MARGIN, BOTTOM, overview_size[0] - 2 * FIGURE_MARGIN, overview_size[1] - TOP - BOTTOM, id='OverviewFigure', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
        ),
    ]
    document.addPageTemplates(sorted(templates, key=lambda item: item.id != first_template))
    document.build(story, canvasmaker=lambda *a, **kw: NumberedCanvas(*a, review_label=review_label, **kw))
    print(json.dumps({
        'output': str(output), 'pages': document.page, 'images': len(figures),
        'unique_links': len(inline.links), 'status': review_label, 'figures': figures,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input', type=Path, default=ROOT / 'docs/analysis-report.md', help='Markdown report, default docs/analysis-report.md')
    parser.add_argument('--output', type=Path, required=True, help='Destination PDF')
    parser.add_argument('--diagram-dir', type=Path, help='Directory of matching PNGs for SVG figures')
    parser.add_argument('--branch', default='analysis_work', help='GitHub branch for relative source links')
    parser.add_argument('--date', default='17 October 2026', help='Revision date displayed in the review footer')
    parser.add_argument('--font-dir', type=Path, help='Optional Arial font directory')
    parser.add_argument('--overview-paper', choices=sorted(OVERVIEW_PAPERS), default='A1', help='Landscape paper for the dense level-1 DFD only (default A1; other figures remain A3)')
    args = parser.parse_args()
    export(args.input, args.output, args.diagram_dir, args.branch, args.date, args.font_dir, args.overview_paper)


if __name__ == '__main__':
    main()
