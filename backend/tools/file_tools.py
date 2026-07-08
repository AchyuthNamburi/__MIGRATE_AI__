# backend/tools/file_tools.py
"""File operations tools"""

import os
import json
from typing import List, Dict, Optional


class FileTools:
    """File operations for the migration agent"""
    
    def __init__(self):
        self.files_read = 0
        self.files_written = 0
    
    def read_file(self, path: str) -> Optional[str]:
        """Read a file"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.files_read += 1
            return content
        except Exception as e:
            return None
    
    def write_file(self, path: str, content: str) -> bool:
        """Write a file"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.files_written += 1
            return True
        except Exception as e:
            return False
    
    def list_files(self, path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """List files in a directory"""
        files = []
        for root, dirs, filenames in os.walk(path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            for filename in filenames:
                if extensions is None or any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
        return files
    
    def read_json(self, path: str) -> Optional[Dict]:
        """Read a JSON file"""
        content = self.read_file(path)
        if content:
            try:
                return json.loads(content)
            except:
                return None
        return None
    
    def write_json(self, path: str, data: Dict) -> bool:
        """Write a JSON file"""
        try:
            content = json.dumps(data, indent=2)
            return self.write_file(path, content)
        except:
            return False
    
    def get_stats(self) -> Dict:
        """Get file operation statistics"""
        return {
            "files_read": self.files_read,
            "files_written": self.files_written
        }