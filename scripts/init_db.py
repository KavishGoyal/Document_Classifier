#!/usr/bin/env python3
"""
Database initialization script
Drops and recreates all tables
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.config import engine, init_db
from database.models import Base
from loguru import logger


def drop_all_tables():
    """Drop all existing tables"""
    logger.warning("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")


def create_all_tables():
    """Create all tables"""
    logger.info("Creating all tables...")
    init_db()
    logger.info("All tables created successfully")


def main():
    """Main function"""
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print()
    
    response = input("⚠️  This will DELETE all existing data. Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    try:
        # Drop tables
        drop_all_tables()
        
        # Create tables
        create_all_tables()
        
        print()
        print("=" * 60)
        print("✅ Database initialized successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()