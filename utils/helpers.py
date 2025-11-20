"""
Utility helper functions
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import re


def get_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate file hash"""
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext


def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension without dot"""
    return Path(filename).suffix.lstrip('.')


def is_pdf_file(filename: str) -> bool:
    """Check if file is a PDF"""
    return get_file_extension(filename).lower() == 'pdf'


def list_files_in_directory(
    directory: str,
    extension: Optional[str] = None,
    recursive: bool = False
) -> List[str]:
    """List files in directory with optional filtering"""
    path = Path(directory)
    
    if not path.exists():
        return []
    
    if recursive:
        pattern = f"**/*.{extension}" if extension else "**/*"
        files = path.glob(pattern)
    else:
        pattern = f"*.{extension}" if extension else "*"
        files = path.glob(pattern)
    
    return [str(f) for f in files if f.is_file()]


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """Save dictionary as JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False


def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None


def format_timestamp(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object"""
    return dt.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse timestamp string"""
    try:
        return datetime.strptime(timestamp_str, format_str)
    except Exception:
        return None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_confidence_score(
    vision_confidence: float,
    text_confidence: float,
    vision_weight: float = 0.3,
    text_weight: float = 0.7
) -> float:
    """Calculate weighted confidence score"""
    return (vision_confidence * vision_weight) + (text_confidence * text_weight)


def normalize_domain_name(domain: str) -> str:
    """Normalize domain name"""
    return domain.lower().strip().replace(' ', '_')


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract top keywords from text (simple frequency-based)"""
    # Remove common words
    common_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Tokenize and filter
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    filtered_words = [w for w in words if w not in common_words]
    
    # Count frequency
    from collections import Counter
    word_freq = Counter(filtered_words)
    
    return [word for word, _ in word_freq.most_common(top_n)]


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """
    Validate file path
    
    Returns:
        (is_valid, error_message)
    """
    if not file_path:
        return False, "File path is empty"
    
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File does not exist: {file_path}"
    
    if not path.is_file():
        return False, f"Path is not a file: {file_path}"
    
    if not is_pdf_file(file_path):
        return False, f"File is not a PDF: {file_path}"
    
    return True, ""


def create_safe_filename(original_name: str, domain: str) -> str:
    """Create safe filename with domain prefix"""
    sanitized = sanitize_filename(original_name)
    name, ext = os.path.splitext(sanitized)
    
    # Add domain prefix if not already present
    if not name.startswith(f"{domain}_"):
        name = f"{domain}_{name}"
    
    return name + ext


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split items into batches"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator for retry with exponential backoff"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
        
        raise last_exception
    
    return wrapper


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def get_percentage(part: int, total: int, decimals: int = 2) -> float:
    """Calculate percentage"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimals)


def time_ago(dt: datetime) -> str:
    """Get human-readable time ago string"""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    else:
        return f"{int(seconds / 86400)} days ago"


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?-]', '', text)
    
    return text.strip()


def validate_confidence(confidence: float) -> float:
    """Validate and normalize confidence score"""
    return max(0.0, min(1.0, confidence))


class ProgressTracker:
    """Simple progress tracker"""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
    
    def get_progress(self) -> float:
        """Get progress percentage"""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
    
    def get_eta(self) -> Optional[str]:
        """Get estimated time remaining"""
        if self.current == 0:
            return None
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.current / elapsed
        remaining = (self.total - self.current) / rate
        
        if remaining < 60:
            return f"{int(remaining)} seconds"
        elif remaining < 3600:
            return f"{int(remaining / 60)} minutes"
        else:
            return f"{int(remaining / 3600)} hours"