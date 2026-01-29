#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the PostgreSQL database tables using SQLModel.
Run this script to set up the database schema before starting the application.

Usage:
    python -m app.init_db

    Or from the backend directory:
    python app/init_db.py
"""
import sys
import os

# Ensure the backend directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel

# Import the database engine
from app.database import engine, DATABASE_URL

# Import ALL models to register them with SQLModel metadata
# This is critical - models must be imported before create_all()
from app.models.sql import User, Application, LoanStage
from app.models.application import LoanApplication


def init_database():
    """
    Initialize the database by creating all tables.

    This function:
    1. Imports all SQLModel table classes
    2. Creates the database tables if they don't exist
    3. Prints status information
    """
    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)
    print(f"Database URL: {DATABASE_URL.split('@')[-1]}")  # Hide credentials
    print()

    print("Registered models:")
    for table_name in SQLModel.metadata.tables.keys():
        print(f"  - {table_name}")
    print()

    print("Creating tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)


def drop_all_tables():
    """
    Drop all tables (USE WITH CAUTION - for development only).
    """
    print("WARNING: This will drop all tables!")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        SQLModel.metadata.drop_all(engine)
        print("All tables dropped.")
    else:
        print("Aborted.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_all_tables()
    else:
        init_database()
