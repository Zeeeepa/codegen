"""File utility functions for the codegen extensions."""

from typing import Dict, Optional, Any

from codegen.sdk.core.file import File


def get_file_metadata(file: File) -> Dict[str, Any]:
    """Get metadata for a file.

    Args:
        file: The file to get metadata for

    Returns:
        Dictionary containing metadata such as language, size, etc.
    """
    # Extract file extension
    extension = file.filepath.split('.')[-1] if '.' in file.filepath else ''
    
    # Map common extensions to languages
    language_map = {
        'py': 'Python',
        'js': 'JavaScript',
        'ts': 'TypeScript',
        'jsx': 'React JSX',
        'tsx': 'React TSX',
        'html': 'HTML',
        'css': 'CSS',
        'scss': 'SCSS',
        'json': 'JSON',
        'md': 'Markdown',
        'yaml': 'YAML',
        'yml': 'YAML',
        'sh': 'Shell',
        'bash': 'Bash',
        'java': 'Java',
        'c': 'C',
        'cpp': 'C++',
        'h': 'C/C++ Header',
        'hpp': 'C++ Header',
        'go': 'Go',
        'rs': 'Rust',
        'rb': 'Ruby',
        'php': 'PHP',
        'swift': 'Swift',
        'kt': 'Kotlin',
        'sql': 'SQL',
        'xml': 'XML',
        'toml': 'TOML',
        'ini': 'INI',
        'conf': 'Configuration',
        'txt': 'Text',
    }
    
    # Determine language based on extension
    language = language_map.get(extension.lower(), 'Unknown')
    
    # Get file size
    size = len(file.content)
    
    # Count lines
    line_count = len(file.content.splitlines())
    
    # Create metadata dictionary
    metadata = {
        'language': language,
        'extension': extension,
        'size': size,
        'line_count': line_count,
        'is_binary': False,  # Assuming text files for now
    }
    
    return metadata