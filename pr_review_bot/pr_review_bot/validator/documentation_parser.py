"""
Documentation Parser for PR Review Agent.
This module provides functionality for parsing documentation files and extracting requirements.
"""
import os
import re
import logging
import markdown
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DocumentationParser:
    """
    Parser for extracting requirements from documentation files.
    
    Extracts structured information like requirements, specifications, and other
    relevant details from documentation files.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the documentation parser.
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = repo_path
        
        # Regular expressions for identifying requirements
        self.requirement_keywords = [
            "must", "should", "shall", "will", "required", "needs to",
            "has to", "need to", "requirement", "mandatory"
        ]
        
        # Regular expression for identifying requirement statements
        self.requirement_pattern = re.compile(
            r"(?:^|\n)(?:\s*[-*•]\s*|\s*\d+\.\s*|\s*)(?P<text>.*?(?:" + 
            "|".join(self.requirement_keywords) + 
            r").*?)(?:\n|$)",
            re.IGNORECASE
        )
        
        # Regular expression for identifying requirement sections
        self.section_pattern = re.compile(
            r"(?:^|\n)#+\s*(?P<title>.*?requirements.*?)(?:\n|$)",
            re.IGNORECASE
        )
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a documentation file and extract requirements.
        
        Args:
            file_path: Path to the documentation file
            
        Returns:
            Parsed documentation data
        """
        try:
            # Check if file exists
            full_path = os.path.join(self.repo_path, file_path)
            if not os.path.exists(full_path):
                logger.warning(f"File not found: {full_path}")
                return {
                    "file_path": file_path,
                    "exists": False,
                    "error": "File not found",
                    "requirements": []
                }
            
            # Read file content
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse file based on extension
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() in [".md", ".markdown"]:
                return self._parse_markdown(file_path, content)
            else:
                return self._parse_text(file_path, content)
        
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return {
                "file_path": file_path,
                "exists": True,
                "error": f"Error parsing file: {str(e)}",
                "requirements": []
            }
    
    def _parse_markdown(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a Markdown file and extract requirements.
        
        Args:
            file_path: Path to the Markdown file
            content: Content of the Markdown file
            
        Returns:
            Parsed documentation data
        """
        try:
            # Convert Markdown to HTML
            html = markdown.markdown(content)
            
            # Parse HTML
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract text
            text = soup.get_text()
            
            # Extract requirements
            requirements = self._extract_requirements(text, file_path)
            
            # Extract sections
            sections = self._extract_sections(soup)
            
            return {
                "file_path": file_path,
                "exists": True,
                "format": "markdown",
                "requirements": requirements,
                "sections": sections
            }
        
        except Exception as e:
            logger.error(f"Error parsing Markdown file {file_path}: {e}")
            return {
                "file_path": file_path,
                "exists": True,
                "format": "markdown",
                "error": f"Error parsing Markdown file: {str(e)}",
                "requirements": []
            }
    
    def _parse_text(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a text file and extract requirements.
        
        Args:
            file_path: Path to the text file
            content: Content of the text file
            
        Returns:
            Parsed documentation data
        """
        try:
            # Extract requirements
            requirements = self._extract_requirements(content, file_path)
            
            return {
                "file_path": file_path,
                "exists": True,
                "format": "text",
                "requirements": requirements
            }
        
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            return {
                "file_path": file_path,
                "exists": True,
                "format": "text",
                "error": f"Error parsing text file: {str(e)}",
                "requirements": []
            }
    
    def _extract_requirements(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """
        Extract requirements from text.
        
        Args:
            text: Text to extract requirements from
            source_file: Source file path
            
        Returns:
            List of requirements
        """
        requirements = []
        
        # Find all requirement statements
        matches = self.requirement_pattern.finditer(text)
        
        for match in matches:
            requirement_text = match.group("text").strip()
            
            # Skip empty requirements
            if not requirement_text:
                continue
            
            # Determine requirement type
            req_type = self._determine_requirement_type(requirement_text)
            
            # Add requirement
            requirements.append({
                "text": requirement_text,
                "source": source_file,
                "type": req_type,
                "keywords": self._extract_keywords(requirement_text)
            })
        
        # Also look for bullet points and numbered lists
        bullet_pattern = re.compile(r"(?:^|\n)(?:\s*[-*•]\s*)(?P<text>.*?)(?:\n|$)")
        numbered_pattern = re.compile(r"(?:^|\n)(?:\s*\d+\.\s*)(?P<text>.*?)(?:\n|$)")
        
        for pattern in [bullet_pattern, numbered_pattern]:
            matches = pattern.finditer(text)
            
            for match in matches:
                requirement_text = match.group("text").strip()
                
                # Skip empty requirements or already found requirements
                if not requirement_text or any(req["text"] == requirement_text for req in requirements):
                    continue
                
                # Check if it contains any requirement keywords
                if any(keyword in requirement_text.lower() for keyword in self.requirement_keywords):
                    # Determine requirement type
                    req_type = self._determine_requirement_type(requirement_text)
                    
                    # Add requirement
                    requirements.append({
                        "text": requirement_text,
                        "source": source_file,
                        "type": req_type,
                        "keywords": self._extract_keywords(requirement_text)
                    })
        
        return requirements
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract sections from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of sections
        """
        sections = []
        
        # Find all headings
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        for heading in headings:
            # Get heading text
            heading_text = heading.get_text().strip()
            
            # Get heading level
            level = int(heading.name[1])
            
            # Get section content
            content = ""
            next_node = heading.next_sibling
            
            while next_node and not (next_node.name and next_node.name.startswith("h") and int(next_node.name[1]) <= level):
                if hasattr(next_node, "get_text"):
                    content += next_node.get_text()
                elif hasattr(next_node, "string") and next_node.string:
                    content += next_node.string
                
                next_node = next_node.next_sibling
            
            # Add section
            sections.append({
                "title": heading_text,
                "level": level,
                "content": content.strip()
            })
        
        return sections
    
    def _determine_requirement_type(self, text: str) -> str:
        """
        Determine the type of requirement.
        
        Args:
            text: Requirement text
            
        Returns:
            Requirement type (functional, non-functional, etc.)
        """
        text_lower = text.lower()
        
        # Check for functional requirements
        functional_keywords = ["shall", "must", "will", "function", "feature", "capability"]
        if any(keyword in text_lower for keyword in functional_keywords):
            return "functional"
        
        # Check for non-functional requirements
        nonfunctional_keywords = ["performance", "security", "usability", "reliability", 
                                 "maintainability", "scalability", "availability"]
        if any(keyword in text_lower for keyword in nonfunctional_keywords):
            return "non-functional"
        
        # Default to functional
        return "functional"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Convert to lowercase
        text_lower = text.lower()
        
        # Extract keywords
        keywords = []
        
        for keyword in self.requirement_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
