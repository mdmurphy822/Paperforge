"""
Paperforge HTML Converter (v2)

Converts Paperforge papers to WCAG 2.2 AA compliant HTML.
- Markdown-first conversion strategy (most complete)
- LaTeX fallback with include resolution
- Per-folder output structure with portable CSS
"""

import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pypandoc
except ImportError:
    print("ERROR: pypandoc not installed. Run: pip install pypandoc_binary")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

PAPERFORGE_ROOT = Path("./Paperforge")
EXPORTS_DIR = PAPERFORGE_ROOT / "exports"
HTML_OUTPUT_DIR = PAPERFORGE_ROOT / "html"
CSS_SOURCE = HTML_OUTPUT_DIR / "css" / "paperforge-wcag.css"
CSS_FILENAME = "paperforge-wcag.css"


@dataclass
class ConversionResult:
    """Result of a single conversion operation."""
    success: bool
    source_path: Path
    source_type: str  # 'markdown' or 'latex'
    output_path: Optional[Path]
    title: str
    content_size: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Title Extraction
# =============================================================================

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'[-\s]+', '-', text)
    text = text.strip('-')
    if len(text) > 60:
        text = text[:60].rsplit('-', 1)[0]
    return text


def extract_title_from_metadata(metadata_path: Path) -> Optional[str]:
    """Extract title from project_metadata.json."""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            title = data.get('title')
            if not title:
                return None

            volume = data.get('volume')
            if volume:
                title = f"{title} Volume {volume}"

            subtitle = data.get('subtitle')
            if subtitle and subtitle not in title and len(subtitle) < 50:
                title = f"{title}: {subtitle}"

            return title
    except (json.JSONDecodeError, IOError):
        return None


def extract_title_from_latex(tex_path: Path) -> Optional[str]:
    """Extract title from LaTeX source file."""
    try:
        content = tex_path.read_text(encoding='utf-8')
    except IOError:
        return None

    patterns = [
        r'\\title\{([^}]+)\}',
        r'\{\\Huge\\bfseries(?:\\color\{[^}]+\})?\s*([^\\}]+)',
        r'pdftitle\s*=\s*\{([^}]+)\}',
        r'\\lhead\{([^}]+)\}',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', title)
            title = re.sub(r'\\[a-zA-Z]+', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            if title and len(title) > 3:
                return title
    return None


def extract_title_from_markdown(md_path: Path) -> Optional[str]:
    """Extract title from Markdown file (first # heading)."""
    try:
        content = md_path.read_text(encoding='utf-8')
        # Look for YAML frontmatter title
        yaml_match = re.search(r'^---\s*\n.*?title:\s*["\']?([^"\'\n]+)', content, re.DOTALL)
        if yaml_match:
            return yaml_match.group(1).strip()
        # Look for first # heading
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
    except IOError:
        pass
    return None


# =============================================================================
# LaTeX Include Resolution
# =============================================================================

def resolve_latex_includes(tex_path: Path, visited: Optional[set] = None) -> str:
    """Recursively resolve \\input{} and \\include{} statements."""
    if visited is None:
        visited = set()

    # Prevent infinite loops
    abs_path = tex_path.resolve()
    if abs_path in visited:
        return f"% [CIRCULAR INCLUDE: {tex_path}]\n"
    visited.add(abs_path)

    try:
        content = tex_path.read_text(encoding='utf-8')
    except IOError as e:
        return f"% [INCLUDE ERROR: {tex_path}: {e}]\n"

    base_dir = tex_path.parent

    def resolve_input(match):
        rel_path = match.group(1)

        # Try various path resolutions
        candidates = []

        # 1. Direct path with/without .tex
        for ext in ['', '.tex']:
            candidates.append(base_dir / f"{rel_path}{ext}")

        # 2. Handle ../ prefix (parent directory)
        if rel_path.startswith('../'):
            rest = rel_path[3:]
            for ext in ['', '.tex']:
                candidates.append(base_dir.parent / f"{rest}{ext}")

        # 3. Check 03_content_development for relative paths
        if not rel_path.startswith('../') and not rel_path.startswith('/'):
            project_root = base_dir.parent  # Go up from 06_final_output
            for ext in ['', '.tex']:
                candidates.append(project_root / "03_content_development" / f"{rel_path}{ext}")

        for full_path in candidates:
            if full_path.exists():
                logger.debug(f"  Resolved: {rel_path} -> {full_path}")
                return resolve_latex_includes(full_path, visited)

        # Not found - keep original
        logger.warning(f"  Include not found: {rel_path}")
        return match.group(0)

    # Match both \input{...} and \include{...}
    pattern = r'\\(?:input|include)\{([^}]+)\}'
    resolved = re.sub(pattern, resolve_input, content)

    return resolved


# =============================================================================
# Paper Discovery
# =============================================================================

def discover_papers(exports_dir: Path) -> List[Dict]:
    """Discover all convertible papers in exports directory."""
    papers = []

    for project_dir in sorted(exports_dir.iterdir()):
        if not project_dir.is_dir():
            continue

        project_id = project_dir.name
        final_output = project_dir / "06_final_output"

        if not final_output.exists():
            continue

        # Check for metadata
        metadata_path = project_dir / "project_metadata.json"
        if not metadata_path.exists():
            metadata_path = None

        # Look for Markdown files first (preferred)
        md_files = list(final_output.glob("*.md"))
        md_priority = ['paper.md', 'book.md', 'master_package.md', 'whitepaper.md']
        selected_md = None
        for preferred in md_priority:
            for md in md_files:
                if md.name == preferred:
                    selected_md = md
                    break
            if selected_md:
                break
        if not selected_md and md_files:
            # Pick largest .md file (most complete)
            selected_md = max(md_files, key=lambda f: f.stat().st_size)

        # Find .tex files
        tex_files = list(final_output.glob("*.tex"))
        tex_priority = ['paper.tex', 'book.tex', 'master_package.tex', 'whitepaper.tex']
        selected_tex = None
        for preferred in tex_priority:
            for tex in tex_files:
                if tex.name == preferred:
                    selected_tex = tex
                    break
            if selected_tex:
                break
        if not selected_tex and tex_files:
            selected_tex = tex_files[0]

        if selected_md or selected_tex:
            papers.append({
                'project_id': project_id,
                'project_dir': project_dir,
                'md_path': selected_md,
                'tex_path': selected_tex,
                'metadata_path': metadata_path,
                'is_subdoc': False
            })

    return papers


# =============================================================================
# HTML Enhancement
# =============================================================================

def enhance_html_wcag(html: str, title: str) -> str:
    """Enhance HTML for WCAG 2.2 AA compliance."""
    soup = BeautifulSoup(html, 'html.parser')

    # Find or create head
    head = soup.find('head')
    if not head:
        head = soup.new_tag('head')
        if soup.html:
            soup.html.insert(0, head)

    # Ensure lang attribute
    if soup.html:
        soup.html['lang'] = 'en'

    # Add viewport meta
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if not viewport:
        viewport = soup.new_tag('meta')
        viewport['name'] = 'viewport'
        viewport['content'] = 'width=device-width, initial-scale=1.0'
        head.append(viewport)

    # Add CSS link (local file in same folder)
    css_link = soup.new_tag('link')
    css_link['rel'] = 'stylesheet'
    css_link['href'] = CSS_FILENAME
    head.append(css_link)

    # Add skip link
    body = soup.find('body')
    if body:
        skip_link = soup.new_tag('a', href='#main-content')
        skip_link['class'] = 'skip-link'
        skip_link.string = 'Skip to main content'
        body.insert(0, skip_link)

    # Find or create main content
    main = soup.find('main')
    if not main:
        main = soup.new_tag('main')
        main['id'] = 'main-content'
        main['role'] = 'main'

        if body:
            for child in list(body.children):
                if child.name != 'a' or 'skip-link' not in child.get('class', []):
                    if hasattr(child, 'extract'):
                        main.append(child.extract())
            body.append(main)
    else:
        main['id'] = 'main-content'
        main['role'] = 'main'

    # Add roles to header/footer
    header = soup.find('header')
    if header:
        header['role'] = 'banner'

    footer = soup.find('footer')
    if footer:
        footer['role'] = 'contentinfo'

    # Add aria-labelledby to sections
    for section in soup.find_all('section'):
        heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            if not heading.get('id'):
                heading['id'] = slugify(heading.get_text()[:50])
            section['aria-labelledby'] = heading['id']

    # Add TOC aria label
    toc = soup.find('nav', id='TOC')
    if toc:
        toc['aria-label'] = 'Table of contents'

    return str(soup)


# =============================================================================
# Converter Class
# =============================================================================

class PaperforgeHTMLConverter:
    """Convert Paperforge papers to WCAG 2.2 AA compliant HTML."""

    def __init__(
        self,
        exports_dir: Path = EXPORTS_DIR,
        output_dir: Path = HTML_OUTPUT_DIR
    ):
        self.exports_dir = Path(exports_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._used_folders: Dict[str, int] = {}

    def get_title(self, paper: Dict) -> str:
        """Extract title from paper."""
        # Try metadata first
        if paper.get('metadata_path') and Path(paper['metadata_path']).exists():
            title = extract_title_from_metadata(paper['metadata_path'])
            if title:
                return title

        # Try Markdown
        if paper.get('md_path'):
            title = extract_title_from_markdown(paper['md_path'])
            if title:
                return title

        # Try LaTeX
        if paper.get('tex_path'):
            title = extract_title_from_latex(paper['tex_path'])
            if title:
                return title

        # Fallback to project ID
        project_id = paper['project_id']
        clean_id = re.sub(r'^\d{8}_\d{6}_', '', project_id)
        clean_id = re.sub(r'^\d{8}_', '', clean_id)
        return clean_id.replace('_', ' ').title()

    def get_folder_name(self, paper: Dict) -> str:
        """Generate folder name: {timestamp}_{slug}."""
        project_id = paper['project_id']
        title = self.get_title(paper)
        slug = slugify(title)

        # Extract timestamp from project_id
        timestamp_match = re.match(r'^(\d{8})_?\d*_?', project_id)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            folder_name = f"{timestamp}_{slug}"
        else:
            folder_name = slug

        # Handle duplicates
        if folder_name in self._used_folders:
            self._used_folders[folder_name] += 1
            folder_name = f"{folder_name}-v{self._used_folders[folder_name]}"
        else:
            self._used_folders[folder_name] = 1

        return folder_name

    def convert_markdown_to_html(self, md_path: Path) -> Tuple[str, List[str]]:
        """Convert Markdown to HTML using pypandoc."""
        errors = []

        args = [
            '--standalone',
            '--mathjax=https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js',
            '--metadata', 'lang=en',
            '--toc',
            '--toc-depth=3',
            '--wrap=none',
        ]

        try:
            html = pypandoc.convert_file(
                str(md_path),
                'html5',
                extra_args=args
            )
            return html, errors
        except Exception as e:
            errors.append(f"Markdown conversion failed: {e}")
            logger.error(f"Markdown conversion failed: {e}")
            return "", errors

    def convert_latex_to_html(
        self,
        tex_path: Path,
        bib_path: Optional[Path] = None,
        resolve_includes: bool = True
    ) -> Tuple[str, List[str]]:
        """Convert LaTeX to HTML, optionally resolving includes."""
        errors = []

        args = [
            '--standalone',
            '--mathjax=https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js',
            '--metadata', 'lang=en',
            '--toc',
            '--toc-depth=3',
            '--wrap=none',
            '--html-q-tags',
        ]

        if bib_path and bib_path.exists():
            args.extend(['--citeproc', f'--bibliography={bib_path}'])

        try:
            if resolve_includes:
                # Resolve includes and convert from string
                logger.debug(f"  Resolving LaTeX includes...")
                resolved_content = resolve_latex_includes(tex_path)
                html = pypandoc.convert_text(
                    resolved_content,
                    'html5',
                    format='latex',
                    extra_args=args
                )
            else:
                html = pypandoc.convert_file(
                    str(tex_path),
                    'html5',
                    extra_args=args
                )
            return html, errors
        except Exception as e:
            errors.append(f"LaTeX conversion failed: {e}")
            logger.error(f"LaTeX conversion failed: {e}")
            return "", errors

    def convert_single(self, paper: Dict) -> ConversionResult:
        """Convert a single paper to HTML."""
        project_id = paper['project_id']
        logger.info(f"Converting: {project_id}")

        title = self.get_title(paper)

        # Determine output folder
        if paper.get('is_subdoc'):
            parts = project_id.split('/')
            if len(parts) > 1:
                parent_folder = self.output_dir / parts[0]
                parent_folder.mkdir(exist_ok=True)
                folder_name = slugify(self.get_title(paper))
                output_folder = parent_folder / folder_name
            else:
                folder_name = self.get_folder_name(paper)
                output_folder = self.output_dir / folder_name
        else:
            folder_name = self.get_folder_name(paper)
            output_folder = self.output_dir / folder_name

        output_folder.mkdir(parents=True, exist_ok=True)
        output_path = output_folder / "index.html"

        # Find bibliography
        bib_path = None
        if paper.get('tex_path'):
            tex_path = Path(paper['tex_path'])
            bib_path = tex_path.parent / "bibliography.bib"
            if not bib_path.exists():
                bib_path = tex_path.parent.parent / "04_citations" / "bibliography.bib"
            if not bib_path.exists():
                bib_path = None

        # Try Markdown first (usually complete)
        html = ""
        source_type = ""
        errors = []

        if paper.get('md_path') and Path(paper['md_path']).exists():
            md_size = Path(paper['md_path']).stat().st_size
            if md_size > 1000:  # At least 1KB
                logger.info(f"  Using Markdown source ({md_size:,} bytes)")
                html, errors = self.convert_markdown_to_html(paper['md_path'])
                source_type = "markdown"

        # Fall back to LaTeX with include resolution
        if not html and paper.get('tex_path') and Path(paper['tex_path']).exists():
            logger.info(f"  Using LaTeX source with include resolution")
            html, errors = self.convert_latex_to_html(
                paper['tex_path'],
                bib_path,
                resolve_includes=True
            )
            source_type = "latex"

        if not html:
            return ConversionResult(
                success=False,
                source_path=paper.get('md_path') or paper.get('tex_path'),
                source_type=source_type or "unknown",
                output_path=None,
                title=title,
                errors=errors or ["No convertible source found"]
            )

        # Enhance HTML for WCAG
        enhanced_html = enhance_html_wcag(html, title)

        # Write output
        try:
            output_path.write_text(enhanced_html, encoding='utf-8')
            content_size = len(enhanced_html)

            # Copy CSS to folder
            if CSS_SOURCE.exists():
                shutil.copy(CSS_SOURCE, output_folder / CSS_FILENAME)

            logger.info(f"  -> {output_path.relative_to(PAPERFORGE_ROOT)} ({content_size:,} bytes)")

            return ConversionResult(
                success=True,
                source_path=paper.get('md_path') or paper.get('tex_path'),
                source_type=source_type,
                output_path=output_path,
                title=title,
                content_size=content_size,
                errors=errors
            )
        except IOError as e:
            errors.append(f"Failed to write output: {e}")
            return ConversionResult(
                success=False,
                source_path=paper.get('md_path') or paper.get('tex_path'),
                source_type=source_type,
                output_path=None,
                title=title,
                errors=errors
            )

    def convert_all(self) -> List[ConversionResult]:
        """Convert all discoverable papers."""
        results = []

        papers = discover_papers(self.exports_dir)
        logger.info(f"Discovered {len(papers)} papers in exports/")

        for paper in papers:
            result = self.convert_single(paper)
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_size = sum(r.content_size for r in results if r.success)

        logger.info(f"\n{'='*60}")
        logger.info(f"Conversion complete: {successful} successful, {failed} failed")
        logger.info(f"Total output size: {total_size:,} bytes")

        # Report by source type
        md_count = sum(1 for r in results if r.success and r.source_type == 'markdown')
        tex_count = sum(1 for r in results if r.success and r.source_type == 'latex')
        logger.info(f"Sources: {md_count} from Markdown, {tex_count} from LaTeX")

        if failed > 0:
            logger.warning("\nFailed conversions:")
            for r in results:
                if not r.success:
                    logger.warning(f"  - {r.title}: {', '.join(r.errors)}")

        # Check for small outputs (potentially incomplete)
        small_outputs = [r for r in results if r.success and r.content_size < 10000]
        if small_outputs:
            logger.warning(f"\n{len(small_outputs)} outputs under 10KB (may be incomplete):")
            for r in small_outputs:
                logger.warning(f"  - {r.title}: {r.content_size:,} bytes")

        return results


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert Paperforge papers to accessible HTML (v2)'
    )
    parser.add_argument(
        '--exports-dir',
        type=Path,
        default=EXPORTS_DIR,
        help='Path to exports directory'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=HTML_OUTPUT_DIR,
        help='Path to HTML output directory'
    )
    parser.add_argument(
        '--single',
        type=str,
        help='Convert single project by ID'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List discoverable papers without converting'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    converter = PaperforgeHTMLConverter(
        exports_dir=args.exports_dir,
        output_dir=args.output_dir
    )

    if args.list:
        papers = discover_papers(args.exports_dir)
        print(f"\nDiscovered {len(papers)} convertible papers:\n")
        for paper in papers:
            title = converter.get_title(paper)
            folder = converter.get_folder_name(paper)
            has_md = "MD" if paper.get('md_path') else "--"
            has_tex = "TEX" if paper.get('tex_path') else "---"
            print(f"  [{has_md}|{has_tex}] {paper['project_id']}")
            print(f"           Title: {title}")
            print(f"           Folder: {folder}/")
            print()
        return

    if args.single:
        papers = discover_papers(args.exports_dir)

        target = None
        for paper in papers:
            if args.single in paper['project_id']:
                target = paper
                break

        if not target:
            print(f"Error: Paper not found: {args.single}")
            sys.exit(1)

        result = converter.convert_single(target)
        if result.success:
            print(f"Converted: {result.output_path} ({result.content_size:,} bytes)")
        else:
            print(f"Failed: {', '.join(result.errors)}")
            sys.exit(1)
    else:
        results = converter.convert_all()
        failed = [r for r in results if not r.success]
        if failed:
            sys.exit(1)


if __name__ == '__main__':
    main()
