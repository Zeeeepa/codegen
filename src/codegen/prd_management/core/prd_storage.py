"""
PRD Storage Service - Handles persistent storage of PRDs
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .prd_template import PRDTemplate, PRDStatus


class PRDStorageService:
    """
    Service for storing and retrieving PRDs
    """
    
    def __init__(self, storage_dir: str = "prd_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.storage_dir / "prds").mkdir(exist_ok=True)
        (self.storage_dir / "reports").mkdir(exist_ok=True)
        (self.storage_dir / "backups").mkdir(exist_ok=True)
    
    async def save_prd(self, prd: PRDTemplate) -> None:
        """
        Save a PRD to storage
        
        Args:
            prd: PRD to save
        """
        
        prd.updated_at = datetime.now().isoformat()
        
        # Save main PRD file
        prd_file = self.storage_dir / "prds" / f"{prd.id}.json"
        
        with open(prd_file, 'w') as f:
            json.dump(prd.to_dict(), f, indent=2)
        
        # Create backup
        await self._create_backup(prd)
    
    async def load_prd(self, prd_id: str) -> Optional[PRDTemplate]:
        """
        Load a PRD from storage
        
        Args:
            prd_id: PRD identifier
            
        Returns:
            PRD template or None if not found
        """
        
        prd_file = self.storage_dir / "prds" / f"{prd_id}.json"
        
        if not prd_file.exists():
            return None
        
        try:
            with open(prd_file, 'r') as f:
                prd_data = json.load(f)
            
            return PRDTemplate.from_dict(prd_data)
            
        except Exception as e:
            print(f"Error loading PRD {prd_id}: {e}")
            return None
    
    async def list_prds(
        self,
        status: Optional[PRDStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List PRDs with optional filtering
        
        Args:
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of PRD summaries
        """
        
        prd_files = list((self.storage_dir / "prds").glob("*.json"))
        prd_summaries = []
        
        for prd_file in prd_files:
            try:
                with open(prd_file, 'r') as f:
                    prd_data = json.load(f)
                
                # Filter by status if specified
                if status and prd_data.get('status') != status.value:
                    continue
                
                # Create summary
                summary = {
                    'id': prd_data['id'],
                    'title': prd_data['title'],
                    'status': prd_data['status'],
                    'created_at': prd_data['created_at'],
                    'updated_at': prd_data['updated_at'],
                    'completion_percentage': self._calculate_completion_percentage(prd_data),
                    'task_count': len(prd_data.get('implementation', {}).get('tasks', []))
                }
                
                prd_summaries.append(summary)
                
            except Exception as e:
                print(f"Error reading PRD file {prd_file}: {e}")
                continue
        
        # Sort by updated_at (most recent first)
        prd_summaries.sort(key=lambda x: x['updated_at'], reverse=True)
        
        # Apply pagination
        return prd_summaries[offset:offset + limit]
    
    async def delete_prd(self, prd_id: str) -> bool:
        """
        Delete a PRD from storage
        
        Args:
            prd_id: PRD identifier
            
        Returns:
            True if deleted, False if not found
        """
        
        prd_file = self.storage_dir / "prds" / f"{prd_id}.json"
        
        if not prd_file.exists():
            return False
        
        try:
            # Move to backup before deleting
            backup_dir = self.storage_dir / "backups" / "deleted"
            backup_dir.mkdir(exist_ok=True)
            
            backup_file = backup_dir / f"{prd_id}_{int(datetime.now().timestamp())}.json"
            prd_file.rename(backup_file)
            
            return True
            
        except Exception as e:
            print(f"Error deleting PRD {prd_id}: {e}")
            return False
    
    async def search_prds(
        self,
        query: str,
        fields: List[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search PRDs by text query
        
        Args:
            query: Search query
            fields: Fields to search in (default: title, goal, what)
            limit: Maximum number of results
            
        Returns:
            List of matching PRD summaries
        """
        
        if fields is None:
            fields = ['title', 'goal', 'what']
        
        query_lower = query.lower()
        prd_files = list((self.storage_dir / "prds").glob("*.json"))
        matching_prds = []
        
        for prd_file in prd_files:
            try:
                with open(prd_file, 'r') as f:
                    prd_data = json.load(f)
                
                # Check if query matches any of the specified fields
                match_found = False
                for field in fields:
                    field_value = prd_data.get(field, '')
                    if isinstance(field_value, str) and query_lower in field_value.lower():
                        match_found = True
                        break
                    elif isinstance(field_value, list):
                        for item in field_value:
                            if isinstance(item, str) and query_lower in item.lower():
                                match_found = True
                                break
                
                if match_found:
                    summary = {
                        'id': prd_data['id'],
                        'title': prd_data['title'],
                        'status': prd_data['status'],
                        'created_at': prd_data['created_at'],
                        'updated_at': prd_data['updated_at'],
                        'completion_percentage': self._calculate_completion_percentage(prd_data),
                        'relevance_score': self._calculate_relevance_score(prd_data, query, fields)
                    }
                    matching_prds.append(summary)
                
            except Exception as e:
                print(f"Error searching PRD file {prd_file}: {e}")
                continue
        
        # Sort by relevance score
        matching_prds.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return matching_prds[:limit]
    
    async def get_prd_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored PRDs
        
        Returns:
            Dictionary with statistics
        """
        
        prd_files = list((self.storage_dir / "prds").glob("*.json"))
        
        stats = {
            'total_prds': len(prd_files),
            'status_counts': {},
            'completion_stats': {
                'completed': 0,
                'in_progress': 0,
                'failed': 0
            },
            'creation_timeline': {},
            'average_task_count': 0,
            'storage_size_mb': 0
        }
        
        total_tasks = 0
        total_size = 0
        
        for prd_file in prd_files:
            try:
                with open(prd_file, 'r') as f:
                    prd_data = json.load(f)
                
                # Count by status
                status = prd_data.get('status', 'unknown')
                stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1
                
                # Completion stats
                completion_pct = self._calculate_completion_percentage(prd_data)
                if completion_pct >= 100:
                    stats['completion_stats']['completed'] += 1
                elif completion_pct > 0:
                    stats['completion_stats']['in_progress'] += 1
                else:
                    stats['completion_stats']['failed'] += 1
                
                # Creation timeline (by month)
                created_at = prd_data.get('created_at', '')
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        month_key = created_date.strftime('%Y-%m')
                        stats['creation_timeline'][month_key] = stats['creation_timeline'].get(month_key, 0) + 1
                    except:
                        pass
                
                # Task count
                task_count = len(prd_data.get('implementation', {}).get('tasks', []))
                total_tasks += task_count
                
                # File size
                total_size += prd_file.stat().st_size
                
            except Exception as e:
                print(f"Error processing PRD file {prd_file}: {e}")
                continue
        
        # Calculate averages
        if stats['total_prds'] > 0:
            stats['average_task_count'] = total_tasks / stats['total_prds']
        
        stats['storage_size_mb'] = total_size / (1024 * 1024)
        
        return stats
    
    async def _create_backup(self, prd: PRDTemplate) -> None:
        """Create a backup of the PRD"""
        
        backup_dir = self.storage_dir / "backups" / prd.id
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = int(datetime.now().timestamp())
        backup_file = backup_dir / f"{prd.id}_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(prd.to_dict(), f, indent=2)
        
        # Keep only last 10 backups
        backup_files = sorted(backup_dir.glob(f"{prd.id}_*.json"))
        if len(backup_files) > 10:
            for old_backup in backup_files[:-10]:
                old_backup.unlink()
    
    def _calculate_completion_percentage(self, prd_data: Dict[str, Any]) -> float:
        """Calculate completion percentage for a PRD"""
        
        tasks = prd_data.get('implementation', {}).get('tasks', [])
        if not tasks:
            return 0.0
        
        completed_tasks = sum(1 for task in tasks if task.get('status') == 'completed')
        return (completed_tasks / len(tasks)) * 100
    
    def _calculate_relevance_score(
        self,
        prd_data: Dict[str, Any],
        query: str,
        fields: List[str]
    ) -> float:
        """Calculate relevance score for search results"""
        
        query_lower = query.lower()
        score = 0.0
        
        # Field weights
        field_weights = {
            'title': 3.0,
            'goal': 2.0,
            'what': 2.0,
            'success_criteria': 1.5,
            'why': 1.0
        }
        
        for field in fields:
            field_value = prd_data.get(field, '')
            weight = field_weights.get(field, 1.0)
            
            if isinstance(field_value, str):
                # Count occurrences
                occurrences = field_value.lower().count(query_lower)
                score += occurrences * weight
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, str):
                        occurrences = item.lower().count(query_lower)
                        score += occurrences * weight
        
        return score
    
    # Utility methods
    def get_storage_path(self) -> Path:
        """Get the storage directory path"""
        return self.storage_dir
    
    def cleanup_old_backups(self, days_old: int = 30) -> int:
        """
        Clean up old backup files
        
        Args:
            days_old: Delete backups older than this many days
            
        Returns:
            Number of files deleted
        """
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        backup_dirs = [
            self.storage_dir / "backups",
            self.storage_dir / "backups" / "deleted"
        ]
        
        for backup_dir in backup_dirs:
            if not backup_dir.exists():
                continue
            
            for backup_file in backup_dir.rglob("*.json"):
                try:
                    if backup_file.stat().st_mtime < cutoff_time:
                        backup_file.unlink()
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting backup file {backup_file}: {e}")
        
        return deleted_count

