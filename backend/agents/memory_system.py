# backend/agents/memory_system.py
"""Memory System - Maintains cross-file context across the migration process"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemorySystem:
    """Stores and retrieves cross-file context during migration"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.memory = {
            "job_id": job_id,
            "project": {},
            "files": {},
            "imports": {},
            "dependencies": {},
            "changes": [],
            "errors": [],
            "confidence": {},
            "stats": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    # ===== PROJECT-LEVEL MEMORY =====
    
    def set_project_info(self, info: dict):
        """Store project-level information"""
        self.memory["project"] = info
        self._update_timestamp()
    
    def get_project_info(self) -> dict:
        """Get project-level information"""
        return self.memory.get("project", {})
    
    # ===== FILE-LEVEL MEMORY =====
    
    def add_file(self, file_path: str, file_info: dict):
        """Store information about a file"""
        self.memory["files"][file_path] = {
            "path": file_path,
            "type": file_info.get("type", "unknown"),
            "imports": file_info.get("imports", []),
            "exports": file_info.get("exports", []),
            "summary": file_info.get("summary", ""),
            "changes": [],
            "confidence": file_info.get("confidence", 0.0),
            "processed_at": datetime.utcnow().isoformat()
        }
        self._update_timestamp()
    
    def get_file(self, file_path: str) -> Optional[dict]:
        """Get information about a specific file"""
        return self.memory["files"].get(file_path)
    
    def get_all_files(self) -> dict:
        """Get all files in memory"""
        return self.memory["files"]
    
    def get_processed_files(self) -> List[str]:
        """Get list of processed files"""
        return [f for f in self.memory["files"].keys()]
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file is already in memory"""
        return file_path in self.memory["files"]
    
    # ===== IMPORT/EXPORT MEMORY =====
    
    def add_import(self, file_path: str, import_name: str):
        """Track an import from a file"""
        if file_path not in self.memory["imports"]:
            self.memory["imports"][file_path] = []
        self.memory["imports"][file_path].append(import_name)
        self._update_timestamp()
    
    def get_imports(self, file_path: str) -> List[str]:
        """Get all imports for a file"""
        return self.memory["imports"].get(file_path, [])
    
    def find_importers(self, module_name: str) -> List[str]:
        """Find all files that import a specific module"""
        result = []
        for file_path, imports in self.memory["imports"].items():
            if module_name in imports:
                result.append(file_path)
        return result
    
    # ===== CHANGE MEMORY =====
    
    def add_change(self, file_path: str, change: dict):
        """Record a change made to a file"""
        self.memory["changes"].append({
            "file": file_path,
            "old": change.get("old"),
            "new": change.get("new"),
            "type": change.get("type", "unknown"),
            "description": change.get("description", ""),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Also update the file's changes list
        if file_path in self.memory["files"]:
            self.memory["files"][file_path]["changes"].append(change)
        
        self._update_timestamp()
    
    def get_changes(self) -> List[dict]:
        """Get all changes made"""
        return self.memory["changes"]
    
    def get_file_changes(self, file_path: str) -> List[dict]:
        """Get changes for a specific file"""
        if file_path in self.memory["files"]:
            return self.memory["files"][file_path].get("changes", [])
        return []
    
    # ===== DEPENDENCY MEMORY =====
    
    def set_dependencies(self, dependencies: dict):
        """Store project dependencies"""
        self.memory["dependencies"] = dependencies
        self._update_timestamp()
    
    def get_dependencies(self) -> dict:
        """Get project dependencies"""
        return self.memory["dependencies"]
    
    # ===== CONFIDENCE MEMORY =====
    
    def set_confidence(self, file_path: str, confidence: float):
        """Set confidence score for a file"""
        self.memory["confidence"][file_path] = confidence
        if file_path in self.memory["files"]:
            self.memory["files"][file_path]["confidence"] = confidence
        self._update_timestamp()
    
    def get_confidence(self, file_path: str) -> float:
        """Get confidence score for a file"""
        return self.memory["confidence"].get(file_path, 0.0)
    
    def get_low_confidence_files(self, threshold: float = 0.7) -> List[str]:
        """Get files with confidence below threshold"""
        return [f for f, c in self.memory["confidence"].items() if c < threshold]
    
    # ===== ERROR MEMORY =====
    
    def add_error(self, file_path: str, error: dict):
        """Record an error for a file"""
        self.memory["errors"].append({
            "file": file_path,
            "error": error.get("message"),
            "type": error.get("type", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        })
        self._update_timestamp()
    
    def get_errors(self) -> List[dict]:
        """Get all errors"""
        return self.memory["errors"]
    
    def get_file_errors(self, file_path: str) -> List[dict]:
        """Get errors for a specific file"""
        return [e for e in self.memory["errors"] if e.get("file") == file_path]
    
    # ===== STATS MEMORY =====
    
    def update_stats(self, stats: dict):
        """Update migration statistics"""
        self.memory["stats"].update(stats)
        self._update_timestamp()
    
    def get_stats(self) -> dict:
        """Get migration statistics"""
        return self.memory["stats"]
    
    # ===== UTILITY METHODS =====
    
    def get_summary(self) -> dict:
        """Get a summary of the current memory state"""
        return {
            "total_files": len(self.memory["files"]),
            "total_changes": len(self.memory["changes"]),
            "total_errors": len(self.memory["errors"]),
            "total_imports": len(self.memory["imports"]),
            "average_confidence": self._average_confidence(),
            "files_with_low_confidence": len(self.get_low_confidence_files())
        }
    
    def _average_confidence(self) -> float:
        """Calculate average confidence across all files"""
        if not self.memory["confidence"]:
            return 0.0
        return sum(self.memory["confidence"].values()) / len(self.memory["confidence"])
    
    def _update_timestamp(self):
        """Update the last modified timestamp"""
        self.memory["updated_at"] = datetime.utcnow().isoformat()
    
    # ===== SAVE/LOAD =====
    
    def to_json(self) -> str:
        """Export memory to JSON"""
        return json.dumps(self.memory, indent=2)
    
    def save_to_file(self, path: str):
        """Save memory to a file"""
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MemorySystem':
        """Load memory from JSON"""
        data = json.loads(json_str)
        memory = cls(data["job_id"])
        memory.memory = data
        return memory
    
    @classmethod
    def from_file(cls, path: str) -> 'MemorySystem':
        """Load memory from a file"""
        with open(path, 'r') as f:
            return cls.from_json(f.read())
    
    # ===== CLEAR =====
    
    def clear(self):
        """Clear all memory"""
        self.memory = {
            "job_id": self.job_id,
            "project": {},
            "files": {},
            "imports": {},
            "dependencies": {},
            "changes": [],
            "errors": [],
            "confidence": {},
            "stats": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def __repr__(self):
        return f"<MemorySystem job_id={self.job_id} files={len(self.memory['files'])}>"