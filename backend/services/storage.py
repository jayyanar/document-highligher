import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from models.document import ProcessingResult, ProcessingStatus
import logging

logger = logging.getLogger(__name__)


class InMemoryStorage:
    """Simple in-memory storage for processing results"""
    
    def __init__(self):
        self.results: Dict[str, ProcessingResult] = {}
        self.storage_dir = os.getenv("STORAGE_DIR", "./storage")
        os.makedirs(self.storage_dir, exist_ok=True)

    async def store_result(self, result: ProcessingResult) -> bool:
        """Store processing result"""
        try:
            self.results[result.transaction_id] = result
            
            # Also persist to file for durability
            file_path = os.path.join(self.storage_dir, f"{result.transaction_id}.json")
            
            # Convert to dict with proper serialization
            result_dict = result.dict()
            
            with open(file_path, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            logger.info(f"Stored result for transaction: {result.transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store result: {e}")
            return False

    async def get_result(self, transaction_id: str) -> Optional[ProcessingResult]:
        """Get processing result by transaction ID"""
        try:
            # Try memory first
            if transaction_id in self.results:
                return self.results[transaction_id]
            
            # Try file storage
            file_path = os.path.join(self.storage_dir, f"{transaction_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                result = ProcessingResult(**data)
                self.results[transaction_id] = result
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None

    async def update_status(self, transaction_id: str, status: ProcessingStatus, 
                          message: Optional[str] = None) -> bool:
        """Update processing status"""
        try:
            result = await self.get_result(transaction_id)
            if result:
                result.status = status
                result.updated_at = datetime.utcnow()
                if message:
                    result.processing_log.append(f"{datetime.utcnow()}: {message}")
                
                await self.store_result(result)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return False

    async def get_all_results(self) -> List[ProcessingResult]:
        """Get all processing results"""
        try:
            # Load any file-based results not in memory
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    transaction_id = filename[:-5]  # Remove .json
                    if transaction_id not in self.results:
                        await self.get_result(transaction_id)
            
            return list(self.results.values())
            
        except Exception as e:
            logger.error(f"Failed to get all results: {e}")
            return []

    async def delete_result(self, transaction_id: str) -> bool:
        """Delete processing result"""
        try:
            # Remove from memory
            if transaction_id in self.results:
                del self.results[transaction_id]
            
            # Remove file
            file_path = os.path.join(self.storage_dir, f"{transaction_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.info(f"Deleted result for transaction: {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete result: {e}")
            return False


# Global storage instance
storage = InMemoryStorage()
