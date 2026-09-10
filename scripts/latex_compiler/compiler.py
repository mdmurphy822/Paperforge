"""
LaTeX Compiler

Handles LaTeX document assembly, template processing, and PDF compilation
with bibliography support and error recovery.
"""

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Template variable pattern
TEMPLATE_VAR_PATTERN = re.compile(r'\{\{(\w+)\}\}')


@dataclass
class CompilationResult:
    """Result of a LaTeX compilation."""
    success: bool
    pdf_path: Optional[Path] = None
    tex_path: Optional[Path] = None
    log_path: Optional[Path] = None
    passes: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    page_count: int = 0
    message: str = ""


@dataclass
class TemplateVariables:
    """Variables for template substitution."""
    title: str = "Untitled Paper"
    author: str = "Unknown Author"
    institution: str = ""
    date: str = ""
    abstract: str = ""
    keywords: str = ""
    bibliography_file: str = "bibliography"

    def to_dict(self) -> Dict[str, str]:
        return {
            "TITLE": self.title,
            "AUTHOR": self.author,
            "INSTITUTION": self.institution,
            "DATE": self.date,
            "ABSTRACT": self.abstract,
            "KEYWORDS": self.keywords,
            "BIBLIOGRAPHY_FILE": self.bibliography_file,
        }


class LaTeXCompiler:
    """Handles LaTeX document compilation."""

    # Tectonic binary path (self-contained LaTeX engine)
    TECTONIC_PATH = Path(__file__).parent.parent.parent / "bin" / "tectonic"

    def __init__(self, templates_path: Path = None, use_tectonic: bool = True):
        """Initialize the compiler."""
        self.templates_path = templates_path or Path(__file__).parent.parent.parent / "templates" / "latex"
        self.use_tectonic = use_tectonic and self.TECTONIC_PATH.exists()
        self._validate_latex_installation()

    def _validate_latex_installation(self) -> bool:
        """Check if LaTeX is installed (Tectonic or pdflatex)."""
        if self.use_tectonic and self.TECTONIC_PATH.exists():
            return True
        try:
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def load_template(self, template_name: str) -> str:
        """
        Load a LaTeX template by name.

        Args:
            template_name: Template path relative to templates dir
                          (e.g., "academic/ieee_conference")

        Returns:
            Template content as string
        """
        template_path = self.templates_path / f"{template_name}.tex"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        return template_path.read_text()

    def process_template(
        self,
        template_content: str,
        variables: TemplateVariables
    ) -> str:
        """
        Substitute variables in template.

        Args:
            template_content: LaTeX template with {{VAR}} placeholders
            variables: TemplateVariables with substitution values

        Returns:
            Processed template content
        """
        result = template_content
        var_dict = variables.to_dict()

        for var_name, value in var_dict.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(value))

        return result

    def assemble_document(
        self,
        template_name: str,
        variables: TemplateVariables,
        sections: List[Path],
        output_path: Path
    ) -> Path:
        """
        Assemble a complete LaTeX document from template and sections.

        Args:
            template_name: Name of template to use
            variables: Template variables
            sections: List of section .tex file paths
            output_path: Where to save the assembled document

        Returns:
            Path to the assembled .tex file
        """
        # Load and process template
        template = self.load_template(template_name)
        processed = self.process_template(template, variables)

        # Find section insertion point
        section_marker = "{{SECTIONS}}"

        if section_marker in processed:
            # Build section includes
            section_includes = []
            for section_path in sorted(sections):
                # Copy section to output directory
                dest_path = output_path.parent / "sections" / section_path.name
                dest_path.parent.mkdir(exist_ok=True)
                shutil.copy(section_path, dest_path)
                section_includes.append(f"\\input{{sections/{section_path.stem}}}")

            sections_content = "\n".join(section_includes)
            processed = processed.replace(section_marker, sections_content)

        # Write assembled document
        output_path.write_text(processed)
        return output_path

    def compile(
        self,
        tex_path: Path,
        output_dir: Path = None,
        runs: int = 3,
        use_bibtex: bool = True
    ) -> CompilationResult:
        """
        Compile a LaTeX document to PDF.

        Args:
            tex_path: Path to the .tex file
            output_dir: Directory for output files (default: same as tex file)
            runs: Number of pdflatex passes (ignored for Tectonic)
            use_bibtex: Whether to run bibtex (ignored for Tectonic)

        Returns:
            CompilationResult with status and paths
        """
        if not tex_path.exists():
            return CompilationResult(
                success=False,
                message=f"TeX file not found: {tex_path}"
            )

        output_dir = output_dir or tex_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get file base name without extension
        base_name = tex_path.stem

        errors = []
        warnings = []
        passes_completed = 0

        try:
            if self.use_tectonic:
                # Tectonic handles everything in one smart pass
                result = self._run_pdflatex(tex_path, output_dir)
                passes_completed = 1
                if result.returncode != 0:
                    errors.extend(self._parse_errors(result.stderr))
                    errors.extend(self._parse_errors(result.stdout))
            else:
                # Traditional pdflatex workflow
                # First pass
                result = self._run_pdflatex(tex_path, output_dir)
                passes_completed += 1
                if result.returncode != 0:
                    errors.extend(self._parse_errors(result.stderr))

                # BibTeX pass (if bibliography exists)
                bib_path = tex_path.parent / "bibliography.bib"
                if use_bibtex and bib_path.exists():
                    self._run_bibtex(base_name, output_dir)

                # Additional passes
                for _ in range(runs - 1):
                    result = self._run_pdflatex(tex_path, output_dir)
                    passes_completed += 1

            # Parse log file
            log_path = output_dir / f"{base_name}.log"
            if log_path.exists():
                log_errors, log_warnings = self._parse_log(log_path)
                errors.extend(log_errors)
                warnings.extend(log_warnings)

            # Check for PDF output
            pdf_path = output_dir / f"{base_name}.pdf"
            if pdf_path.exists():
                page_count = self._get_page_count(pdf_path)
                return CompilationResult(
                    success=True,
                    pdf_path=pdf_path,
                    tex_path=tex_path,
                    log_path=log_path,
                    passes=passes_completed,
                    errors=errors[:5],  # Limit errors
                    warnings=warnings[:10],
                    page_count=page_count,
                    message="Compilation successful" + (" (Tectonic)" if self.use_tectonic else "")
                )
            else:
                return CompilationResult(
                    success=False,
                    tex_path=tex_path,
                    log_path=log_path,
                    passes=passes_completed,
                    errors=errors,
                    warnings=warnings,
                    message="PDF not generated"
                )

        except Exception as e:
            return CompilationResult(
                success=False,
                message=str(e),
                errors=[str(e)]
            )

    def _run_pdflatex(
        self,
        tex_path: Path,
        output_dir: Path
    ) -> subprocess.CompletedProcess:
        """Run pdflatex or Tectonic command."""
        if self.use_tectonic:
            # Use Tectonic (self-contained LaTeX engine)
            return subprocess.run(
                [
                    str(self.TECTONIC_PATH),
                    "--outdir", str(output_dir),
                    "--keep-logs",
                    str(tex_path)
                ],
                capture_output=True,
                text=True,
                cwd=str(tex_path.parent)
            )
        else:
            # Fall back to system pdflatex
            return subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory", str(output_dir),
                    str(tex_path)
                ],
                capture_output=True,
                text=True,
                cwd=str(tex_path.parent)
            )

    def _run_bibtex(self, base_name: str, work_dir: Path) -> subprocess.CompletedProcess:
        """Run bibtex command."""
        return subprocess.run(
            ["bibtex", base_name],
            capture_output=True,
            text=True,
            cwd=str(work_dir)
        )

    def _parse_log(self, log_path: Path) -> Tuple[List[str], List[str]]:
        """Parse LaTeX log file for errors and warnings."""
        errors = []
        warnings = []

        content = log_path.read_text(errors='ignore')

        # Find errors
        error_matches = re.findall(r'^! (.+)$', content, re.MULTILINE)
        errors.extend(error_matches)

        # Find warnings
        warning_matches = re.findall(r'LaTeX Warning: (.+)', content)
        warnings.extend(warning_matches)

        # Find undefined references
        undefined = re.findall(r'Citation `([^\']+)\' undefined', content)
        for ref in undefined:
            warnings.append(f"Undefined citation: {ref}")

        return errors, warnings

    def _parse_errors(self, stderr: str) -> List[str]:
        """Parse errors from stderr."""
        errors = []
        for line in stderr.split('\n'):
            if line.startswith('!') or 'error' in line.lower():
                errors.append(line.strip())
        return errors

    def _get_page_count(self, pdf_path: Path) -> int:
        """Get page count from PDF."""
        try:
            result = subprocess.run(
                ["pdfinfo", str(pdf_path)],
                capture_output=True,
                text=True
            )
            match = re.search(r'Pages:\s+(\d+)', result.stdout)
            if match:
                return int(match.group(1))
        except FileNotFoundError:
            pass
        return 0

    def cleanup_auxiliary_files(self, output_dir: Path, base_name: str):
        """Remove auxiliary LaTeX files."""
        extensions = ['.aux', '.bbl', '.blg', '.out', '.toc', '.lof', '.lot']
        for ext in extensions:
            aux_file = output_dir / f"{base_name}{ext}"
            if aux_file.exists():
                aux_file.unlink()


class DocumentAssembler:
    """Assembles LaTeX documents from sections."""

    def __init__(self, compiler: LaTeXCompiler = None):
        self.compiler = compiler or LaTeXCompiler()

    def assemble_paper(
        self,
        project_path: Path,
        template_name: str,
        metadata: Dict[str, str]
    ) -> Path:
        """
        Assemble a complete paper from project contents.

        Args:
            project_path: Path to the Paperforge project
            template_name: Template to use
            metadata: Paper metadata (title, author, etc.)

        Returns:
            Path to assembled .tex file
        """
        content_dir = project_path / "03_content_development"
        output_dir = project_path / "06_final_output"
        output_dir.mkdir(exist_ok=True)

        # Collect sections
        sections = sorted(content_dir.glob("section_*.tex"))

        # Create template variables
        variables = TemplateVariables(
            title=metadata.get("title", "Untitled"),
            author=metadata.get("author", "Unknown"),
            institution=metadata.get("institution", ""),
            date=metadata.get("date", ""),
            keywords=metadata.get("keywords", ""),
        )

        # Extract abstract if present
        abstract_file = content_dir / "section_00_abstract.tex"
        if abstract_file.exists():
            abstract_content = abstract_file.read_text()
            # Remove LaTeX commands, keep just text
            abstract_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', abstract_content)
            abstract_text = re.sub(r'\\[a-zA-Z]+', '', abstract_text)
            variables.abstract = abstract_text.strip()

        # Copy bibliography if exists
        bib_src = project_path / "04_citations" / "bibliography.bib"
        bib_dest = output_dir / "bibliography.bib"
        if bib_src.exists():
            shutil.copy(bib_src, bib_dest)

        # Assemble document — use title-derived filename
        title = metadata.get("title", "paper")
        slug = re.sub(r'[^\w\s-]', '', title).replace(" ", "_")[:80]
        tex_path = output_dir / f"{slug}.tex" if slug else output_dir / "paper.tex"
        return self.compiler.assemble_document(
            template_name,
            variables,
            sections,
            tex_path
        )


def compile_project(
    project_path: Path,
    template: str = "academic/preprint"
) -> CompilationResult:
    """
    High-level function to compile a Paperforge project.

    Args:
        project_path: Path to the project directory
        template: Template name to use

    Returns:
        CompilationResult with compilation status
    """
    import json

    # Load project metadata
    metadata_file = project_path / "project_metadata.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # Initialize compiler and assembler
    compiler = LaTeXCompiler()
    assembler = DocumentAssembler(compiler)

    # Assemble document
    try:
        tex_path = assembler.assemble_paper(project_path, template, metadata)
    except FileNotFoundError as e:
        return CompilationResult(
            success=False,
            message=f"Template error: {e}"
        )

    # Compile to PDF
    output_dir = project_path / "06_final_output"
    return compiler.compile(tex_path, output_dir)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python compiler.py <tex_file_or_project_path>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.suffix == ".tex":
        # Compile single file
        compiler = LaTeXCompiler()
        result = compiler.compile(path)
    else:
        # Compile project
        result = compile_project(path)

    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.pdf_path:
        print(f"PDF: {result.pdf_path}")
    if result.errors:
        print(f"Errors: {result.errors}")
