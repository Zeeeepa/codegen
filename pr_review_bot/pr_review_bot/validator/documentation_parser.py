"""
Documentation Parser for PR Review Agent.
This module provides functionality for parsing documentation files and extracting
requirements and specifications.
"""
import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import markdown
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)
class DocumentationParser:
    """
    Parser for documentation files.
    
    Extracts requirements, specifications, and other relevant information from
    documentation files like README.md, STRUCTURE.md, and PLAN.md.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the documentation parser.
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = repo_path
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a documentation file and extract structured information.
        
        Args:
            file_path: Path to the documentation file
            
        Returns:
            Dictionary with extracted information
        """
        full_path = os.path.join(self.repo_path, file_path)
        
        if not os.path.exists(full_path):
            logger.warning(f"Documentation file not found: {full_path}")
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Determine file type based on extension
            if file_path.endswith(".md"):
                return self._parse_markdown(content, file_path)
            elif file_path.endswith(".txt"):
                return self._parse_text(content, file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                return {"error": f"Unsupported file type: {file_path}"}
        
        except Exception as e:
            logger.error(f"Error parsing documentation file {file_path}: {e}")
            return {"error": f"Error parsing file: {str(e)}"}
    
    def _parse_markdown(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parse a Markdown file and extract structured information.
        
        Args:
            content: Content of the Markdown file
            file_path: Path to the file (for reference)
            
        Returns:
            Dictionary with extracted information
        """
        result = {
            "file_path": file_path,
            "type": "markdown",
            "title": "",
            "sections": [],
            "requirements": [],
            "code_blocks": [],
            "links": [],
            "todos": []
        }
        
        # Extract title (first h1)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            result["title"] = title_match.group(1).strip()
        
        # Convert markdown to HTML for easier parsing
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract sections
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            section_text = heading.get_text().strip()
            
            # Get content until next heading of same or higher level
            content = []
            sibling = heading.next_sibling
            while sibling and not (sibling.name and sibling.name[0] == 'h' and int(sibling.name[1]) <= level):
                if sibling.string and sibling.string.strip():
                    content.append(sibling.string.strip())
                sibling = sibling.next_sibling
            
            section_content = " ".join(content).strip()
            
            result["sections"].append({
                "level": level,
                "title": section_text,
                "content": section_content
            })
        
        # Extract requirements
        # Look for bullet points or numbered lists that might contain requirements
        for list_item in soup.find_all('li'):
            text = list_item.get_text().strip()
            
            # Check if it looks like a requirement
            if re.search(r'(must|should|shall|will|require|need)', text, re.IGNORECASE):
                result["requirements"].append({
                    "text": text,
                    "type": "functional" if re.search(r'(function|behavior|action)', text, re.IGNORECASE) else "non-functional"
                })
        
        # Extract code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
        for block in code_blocks:
            result["code_blocks"].append(block.strip())
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, url in links:
            result["links"].append({
                "text": text,
                "url": url
            })
        
        # Extract TODOs
        todos = re.findall(r'(?:TODO|FIXME)(?:\([^)]+\))?\s*:?\s*([^\n]+)', content, re.IGNORECASE)
        for todo in todos:
            result["todos"].append(todo.strip())
        
        return result
    
    def _parse_text(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Parse a plain text file and extract structured information.
        
        Args:
            content: Content of the text file
            file_path: Path to the file (for reference)
            
        Returns:
            Dictionary with extracted information
        """
        result = {
            "file_path": file_path,
            "type": "text",
            "title": "",
            "sections": [],
            "requirements": [],
            "todos": []
        }
        
        # Extract title (first non-empty line)
        lines = content.split("\n")
        for line in lines:
            if line.strip():
                result["title"] = line.strip()
                break
        
        # Extract sections (lines that are all caps or have trailing colons)
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.isupper() or line.endswith(":"):
                # Save previous section if exists
                if current_section:
                    result["sections"].append({
                        "title": current_section,
                        "content": "\n".join(section_content).strip()
                    })
                
                # Start new section
                current_section = line.rstrip(":")
                section_content = []
            else:
                section_content.append(line)
        
        # Save last section
        if current_section:
            result["sections"].append({
                "title": current_section,
                "content": "\n".join(section_content).strip()
            })
        
        # Extract requirements
        for line in lines:
            line = line.strip()
            if re.search(r'(must|should|shall|will|require|need)', line, re.IGNORECASE):
                result["requirements"].append({
                    "text": line,
                    "type": "functional" if re.search(r'(function|behavior|action)', line, re.IGNORECASE) else "non-functional"
                })
        
        # Extract TODOs
        todos = re.findall(r'(?:TODO|FIXME)(?:\([^)]+\))?\s*:?\s*([^\n]+)', content, re.IGNORECASE)
        for todo in todos:
            result["todos"].append(todo.strip())
        
        return result
    
    def extract_requirements(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Extract requirements from multiple documentation files.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of requirements extracted from the files
        """
        requirements = []
        
        for file_path in file_paths:
            parsed = self.parse_file(file_path)
            
            if "error" in parsed:
                logger.warning(f"Error parsing {file_path}: {parsed['error']}")
                continue
            
            if "requirements" in parsed:
                for req in parsed["requirements"]:
                    req["source_file"] = file_path
                    requirements.append(req)
        
        return requirements