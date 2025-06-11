import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "document_extraction")
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index on transaction_id for quick lookups
            await self.database.processing_results.create_index("transaction_id", unique=True)
            
            # Index on status for filtering
            await self.database.processing_results.create_index("status")
            
            # Index on created_at for sorting
            await self.database.processing_results.create_index("created_at")
            
            # Compound index for element queries
            await self.database.processing_results.create_index([
                ("transaction_id", 1),
                ("extracted_elements.id", 1)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def get_sync_client(self):
        """Get synchronous MongoDB client for non-async operations"""
        return MongoClient(self.mongodb_url)[self.database_name]


# Global database manager instance
db_manager = DatabaseManager()


async def get_database():
    """Dependency to get database instance"""
    if not db_manager.database:
        await db_manager.connect()
    return db_manager.database
