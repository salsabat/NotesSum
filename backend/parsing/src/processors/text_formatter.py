"""
Text formatter for converting OCR results to RAG-friendly text format
"""

from typing import Dict, List, Any
from pathlib import Path
import json

class TextFormatter:
    """Convert OCR results to clean, readable text format optimized for RAG"""
    
    def __init__(self):
        self.section_separator = "\n" + "="*50 + "\n"
        self.page_separator = "\n" + "-"*30 + "\n"
    
    def format_results(self, results: Dict[str, Any]) -> str:
        """
        Convert OCR results to formatted text
        
        Args:
            results: OCR results dictionary
            
        Returns:
            Formatted text string
        """
        output_lines = []
        
        # Document header
        file_name = Path(results.get('file_path', 'Unknown')).stem
        output_lines.append(f"DOCUMENT: {file_name}")
        output_lines.append(self.section_separator)
        
        # Document summary
        summary = results.get('summary', {})
        output_lines.append("DOCUMENT SUMMARY:")
        output_lines.append(f"Total Pages: {summary.get('total_pages', 0)}")
        output_lines.append(f"Text Regions: {summary.get('text_regions', 0)}")
        output_lines.append(f"Tables: {summary.get('tables', 0)}")
        output_lines.append(f"Equations: {summary.get('equations', 0)}")
        output_lines.append(f"Diagrams: {summary.get('diagrams', 0)}")
        output_lines.append(self.section_separator)
        
        # Process each page
        pages = results.get('pages', [])
        for page in pages:
            page_text = self._format_page(page)
            if page_text.strip():
                output_lines.append(page_text)
                output_lines.append(self.page_separator)
        
        return '\n'.join(output_lines)
    
    def _format_page(self, page: Dict[str, Any]) -> str:
        """Format a single page"""
        output_lines = []
        
        page_num = page.get('page_number', 'Unknown')
        output_lines.append(f"PAGE {page_num}")
        output_lines.append("")
        
        regions = page.get('regions', [])
        
        # Group regions by type for better organization
        text_regions = [r for r in regions if r.get('type') == 'text']
        table_regions = [r for r in regions if r.get('type') == 'table']
        equation_regions = [r for r in regions if r.get('type') == 'equation']
        diagram_regions = [r for r in regions if r.get('type') == 'diagram']
        code_regions = [r for r in regions if r.get('type') == 'code']
        
        # Format text content
        if text_regions:
            for region in text_regions:
                content = region.get('content', '').strip()
                if content:
                    output_lines.append(content)
                    output_lines.append("")
        
        # Format tables
        if table_regions:
            output_lines.append("TABLES:")
            for i, region in enumerate(table_regions, 1):
                table_text = self._format_table(region, i)
                if table_text:
                    output_lines.append(table_text)
                    output_lines.append("")
        
        # Format equations
        if equation_regions:
            output_lines.append("MATHEMATICAL EQUATIONS:")
            for i, region in enumerate(equation_regions, 1):
                equation_text = self._format_equation(region, i)
                if equation_text:
                    output_lines.append(equation_text)
                    output_lines.append("")
        
        # Format code blocks
        if code_regions:
            output_lines.append("CODE BLOCKS:")
            for i, region in enumerate(code_regions, 1):
                code_text = self._format_code(region, i)
                if code_text:
                    output_lines.append(code_text)
                    output_lines.append("")
        
        # Format diagrams
        if diagram_regions:
            output_lines.append("DIAGRAMS AND CHARTS:")
            for i, region in enumerate(diagram_regions, 1):
                diagram_text = self._format_diagram(region, i)
                if diagram_text:
                    output_lines.append(diagram_text)
                    output_lines.append("")
        
        return '\n'.join(output_lines)
    
    def _format_table(self, region: Dict[str, Any], table_num: int) -> str:
        """Format table data as readable text"""
        lines = [f"Table {table_num}:"]
        
        table_data = region.get('data', [])
        if not table_data:
            return ""
        
        # Convert table to readable format
        for row_idx, row in enumerate(table_data):
            if row_idx == 0:
                # Header row
                lines.append("Headers: " + " | ".join(str(cell) for cell in row))
                lines.append("-" * 40)
            else:
                # Data rows
                lines.append("Row {}: {}".format(row_idx, " | ".join(str(cell) for cell in row)))
        
        # Add metadata
        confidence = region.get('confidence', 0)
        lines.append(f"(Confidence: {confidence:.2f}, Rows: {region.get('rows', 0)}, Columns: {region.get('columns', 0)})")
        
        return '\n'.join(lines)
    
    def _format_equation(self, region: Dict[str, Any], eq_num: int) -> str:
        """Format equation as readable text"""
        lines = [f"Equation {eq_num}:"]
        
        # LaTeX format if available
        latex = region.get('latex', '')
        if latex:
            lines.append(f"LaTeX: {latex}")
        
        # Plain text representation if available
        content = region.get('content', '')
        if content and content != latex:
            lines.append(f"Text: {content}")
        
        confidence = region.get('confidence', 0)
        lines.append(f"(Confidence: {confidence:.2f})")
        
        return '\n'.join(lines)
    
    def _format_code(self, region: Dict[str, Any], code_num: int) -> str:
        """Format code block as readable text"""
        lines = [f"Code Block {code_num}:"]
        
        language = region.get('language', 'unknown')
        lines.append(f"Language: {language}")
        
        content = region.get('content', '')
        if content:
            lines.append("Code:")
            # Indent code content
            code_lines = content.split('\n')
            for line in code_lines:
                lines.append(f"    {line}")
        
        confidence = region.get('confidence', 0)
        lines.append(f"(Confidence: {confidence:.2f})")
        
        return '\n'.join(lines)
    
    def _format_diagram(self, region: Dict[str, Any], diagram_num: int) -> str:
        """Format diagram description as readable text"""
        lines = [f"Diagram/Chart {diagram_num}:"]
        
        description = region.get('description', '')
        if description:
            lines.append(f"Description: {description}")
        
        confidence = region.get('confidence', 0)
        lines.append(f"(Confidence: {confidence:.2f})")
        
        return '\n'.join(lines)
    
    def format_for_rag(self, results: Dict[str, Any]) -> str:
        """
        Format results specifically optimized for RAG systems
        
        Args:
            results: OCR results dictionary
            
        Returns:
            RAG-optimized text string
        """
        output_lines = []
        
        # Simple document identifier
        file_name = Path(results.get('file_path', 'Unknown')).stem
        output_lines.append(f"Document: {file_name}")
        output_lines.append("")
        
        # Extract all text content in reading order
        pages = results.get('pages', [])
        for page in pages:
            regions = page.get('regions', [])
            
            # Process regions in order of appearance
            for region in regions:
                region_type = region.get('type', 'unknown')
                
                if region_type == 'text':
                    content = region.get('content', '').strip()
                    if content:
                        output_lines.append(content)
                        output_lines.append("")
                
                elif region_type == 'table':
                    # Convert table to natural language
                    table_text = self._table_to_natural_language(region)
                    if table_text:
                        output_lines.append(table_text)
                        output_lines.append("")
                
                elif region_type == 'equation':
                    # Include equation context
                    latex = region.get('latex', '')
                    if latex:
                        output_lines.append(f"Mathematical equation: {latex}")
                        output_lines.append("")
                
                elif region_type == 'code':
                    # Include code with context
                    content = region.get('content', '')
                    language = region.get('language', 'unknown')
                    if content:
                        output_lines.append(f"Code snippet in {language}:")
                        output_lines.append(content)
                        output_lines.append("")
                
                elif region_type == 'diagram':
                    # Include diagram description
                    description = region.get('description', '')
                    if description:
                        output_lines.append(f"Diagram or chart: {description}")
                        output_lines.append("")
        
        return '\n'.join(output_lines)
    
    def _table_to_natural_language(self, region: Dict[str, Any]) -> str:
        """Convert table data to natural language description"""
        table_data = region.get('data', [])
        if not table_data:
            return ""
        
        lines = []
        
        if len(table_data) > 1:
            headers = table_data[0]
            data_rows = table_data[1:]
            
            lines.append(f"Table with columns: {', '.join(headers)}")
            
            # Describe a few sample rows
            for i, row in enumerate(data_rows[:3]):  # First 3 rows
                row_desc = []
                for j, cell in enumerate(row):
                    if j < len(headers) and cell.strip():
                        row_desc.append(f"{headers[j]}: {cell}")
                
                if row_desc:
                    lines.append(f"Row {i+1} - {', '.join(row_desc)}")
            
            if len(data_rows) > 3:
                lines.append(f"... and {len(data_rows) - 3} more rows")
        
        return '\n'.join(lines)

def convert_json_to_text(json_file_path: str, output_format: str = 'readable') -> str:
    """
    Convert existing JSON results to text format
    
    Args:
        json_file_path: Path to JSON results file
        output_format: 'readable' or 'rag' format
        
    Returns:
        Formatted text string
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        formatter = TextFormatter()
        
        if output_format == 'rag':
            return formatter.format_for_rag(results)
        else:
            return formatter.format_results(results)
    
    except Exception as e:
        return f"Error converting JSON to text: {e}"