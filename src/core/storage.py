"""
Storage management for Stressor.
"""

import json
import sqlite3
import pickle
import gzip
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class TestRun(Base):
    """Database model for test runs."""
    __tablename__ = 'test_runs'
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(255), unique=True, nullable=False)
    model_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON)
    results = Column(JSON)
    meta = Column("metadata", JSON)


class TestCase(Base):
    """Database model for test cases."""
    __tablename__ = 'test_cases'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    input_data = Column(Text, nullable=False)
    expected_output = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON)


class TestResult(Base):
    """Database model for test results."""
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True)
    test_run_id = Column(String(255), nullable=False)
    test_case_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    input_data = Column(Text)
    output_data = Column(Text)
    error_message = Column(Text)
    latency = Column(Integer)  # in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
    meta = Column("metadata", JSON)


class StorageManager:
    """Manages data storage and persistence for FailProof LLM."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize the storage manager.
        
        Args:
            database_url: Database URL (defaults to settings)
        """
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
        
        # Create storage directories
        self.data_dir = Path(settings.data_directory)
        self.backup_dir = Path(settings.backup_directory)
        self._create_directories()
        
        logger.info(f"Storage manager initialized with database: {self.database_url}")
    
    def _initialize_database(self):
        """Initialize database connection and create tables."""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=settings.debug,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _create_directories(self):
        """Create necessary storage directories."""
        directories = [self.data_dir, self.backup_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def save_test_run(self, run_data: Dict[str, Any]) -> str:
        """
        Save a test run to the database.
        
        Args:
            run_data: Test run data
            
        Returns:
            Run ID
        """
        try:
            with self.get_session() as session:
                test_run = TestRun(
                    run_id=run_data['run_id'],
                    model_name=run_data['model_name'],
                    status=run_data['status'],
                    config=run_data.get('config', {}),
                    results=run_data.get('results', {}),
                    meta=run_data.get('metadata', {})
                )
                session.add(test_run)
                session.commit()
                
                logger.info(f"Test run saved: {run_data['run_id']}")
                return run_data['run_id']
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to save test run: {e}")
            raise
    
    def save_test_case(self, test_case_data: Dict[str, Any]) -> str:
        """
        Save a test case to the database.
        
        Args:
            test_case_data: Test case data
            
        Returns:
            Test ID
        """
        try:
            with self.get_session() as session:
                test_case = TestCase(
                    test_id=test_case_data['test_id'],
                    category=test_case_data['category'],
                    name=test_case_data['name'],
                    description=test_case_data.get('description', ''),
                    input_data=test_case_data['input_data'],
                    expected_output=test_case_data.get('expected_output'),
                    tags=test_case_data.get('tags', [])
                )
                session.add(test_case)
                session.commit()
                
                logger.info(f"Test case saved: {test_case_data['test_id']}")
                return test_case_data['test_id']
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to save test case: {e}")
            raise
    
    def save_test_result(self, result_data: Dict[str, Any]) -> int:
        """
        Save a test result to the database.
        
        Args:
            result_data: Test result data
            
        Returns:
            Result ID
        """
        try:
            with self.get_session() as session:
                test_result = TestResult(
                    test_run_id=result_data['test_run_id'],
                    test_case_id=result_data['test_case_id'],
                    status=result_data['status'],
                    input_data=result_data.get('input_data', ''),
                    output_data=result_data.get('output_data', ''),
                    error_message=result_data.get('error_message', ''),
                    latency=result_data.get('latency', 0),
                    meta=result_data.get('metadata', {})
                )
                session.add(test_result)
                session.commit()
                
                logger.debug(f"Test result saved for run: {result_data['test_run_id']}")
                return test_result.id
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to save test result: {e}")
            raise
    
    def get_test_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a test run by ID.
        
        Args:
            run_id: Test run ID
            
        Returns:
            Test run data or None
        """
        try:
            with self.get_session() as session:
                test_run = session.query(TestRun).filter(TestRun.run_id == run_id).first()
                if test_run:
                    return {
                        'run_id': test_run.run_id,
                        'model_name': test_run.model_name,
                        'status': test_run.status,
                        'created_at': test_run.created_at.isoformat(),
                        'updated_at': test_run.updated_at.isoformat(),
                        'config': test_run.config or {},
                        'results': test_run.results or {},
                        'metadata': test_run.meta or {}
                    }
                return None
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve test run: {e}")
            return None
    
    def get_test_results(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve test results for a specific run.
        
        Args:
            run_id: Test run ID
            
        Returns:
            List of test results
        """
        try:
            with self.get_session() as session:
                results = session.query(TestResult).filter(TestResult.test_run_id == run_id).all()
                return [
                    {
                        'id': result.id,
                        'test_case_id': result.test_case_id,
                        'status': result.status,
                        'input_data': result.input_data,
                        'output_data': result.output_data,
                        'error_message': result.error_message,
                        'latency': result.latency,
                        'created_at': result.created_at.isoformat(),
                        'metadata': result.meta or {}
                    }
                    for result in results
                ]
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve test results: {e}")
            return []
    
    def save_json_data(self, filename: str, data: Dict[str, Any], compress: bool = True) -> Path:
        """
        Save data as JSON file.
        
        Args:
            filename: Target filename
            data: Data to save
            compress: Whether to compress the file
            
        Returns:
            Path to saved file
        """
        file_path = self.data_dir / filename
        
        try:
            if compress:
                file_path = file_path.with_suffix(file_path.suffix + '.gz')
                with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"JSON data saved: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Failed to save JSON data: {e}")
            raise
    
    def load_json_data(self, filename: str, compress: bool = True) -> Dict[str, Any]:
        """
        Load data from JSON file.
        
        Args:
            filename: Source filename
            compress: Whether the file is compressed
            
        Returns:
            Loaded data
        """
        file_path = self.data_dir / filename
        
        try:
            if compress:
                file_path = file_path.with_suffix(file_path.suffix + '.gz')
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            logger.debug(f"JSON data loaded: {file_path}")
            return data
        
        except Exception as e:
            logger.error(f"Failed to load JSON data: {e}")
            raise
    
    def save_pickle_data(self, filename: str, data: Any, compress: bool = True) -> Path:
        """
        Save data as pickle file.
        
        Args:
            filename: Target filename
            data: Data to save
            compress: Whether to compress the file
            
        Returns:
            Path to saved file
        """
        file_path = self.data_dir / filename
        
        try:
            if compress:
                file_path = file_path.with_suffix(file_path.suffix + '.gz')
                with gzip.open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            else:
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            
            logger.debug(f"Pickle data saved: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Failed to save pickle data: {e}")
            raise
    
    def load_pickle_data(self, filename: str, compress: bool = True) -> Any:
        """
        Load data from pickle file.
        
        Args:
            filename: Source filename
            compress: Whether the file is compressed
            
        Returns:
            Loaded data
        """
        file_path = self.data_dir / filename
        
        try:
            if compress:
                file_path = file_path.with_suffix(file_path.suffix + '.gz')
                with gzip.open(file_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            
            logger.debug(f"Pickle data loaded: {file_path}")
            return data
        
        except Exception as e:
            logger.error(f"Failed to load pickle data: {e}")
            raise
    
    def create_backup(self, backup_name: str = None) -> Path:
        """
        Create a backup of the database and data files.
        
        Args:
            backup_name: Name for the backup (defaults to timestamp)
            
        Returns:
            Path to backup directory
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Backup database
            if self.database_url.startswith('sqlite'):
                db_path = Path(self.database_url.replace('sqlite:///', ''))
                if db_path.exists():
                    shutil.copy2(db_path, backup_path / db_path.name)
            
            # Backup data directory
            data_backup_path = backup_path / 'data'
            if self.data_dir.exists():
                shutil.copytree(self.data_dir, data_backup_path, dirs_exist_ok=True)
            
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """
        Clean up old backup files.
        
        Args:
            days_to_keep: Number of days to keep backups
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    # Check if backup is old enough to delete
                    # This is a simple check - you might want to implement more sophisticated logic
                    if backup_dir.name.startswith('backup_'):
                        try:
                            backup_date_str = backup_dir.name.replace('backup_', '')
                            backup_date = datetime.strptime(backup_date_str, '%Y%m%d_%H%M%S')
                            if backup_date < cutoff_date:
                                shutil.rmtree(backup_dir)
                                logger.info(f"Deleted old backup: {backup_dir}")
                        except ValueError:
                            # Skip directories that don't match the naming pattern
                            continue
        
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def export_to_csv(self, run_id: str, output_path: Path = None) -> Path:
        """
        Export test results to CSV.
        
        Args:
            run_id: Test run ID
            output_path: Output path (defaults to data directory)
            
        Returns:
            Path to exported CSV file
        """
        if output_path is None:
            output_path = self.data_dir / f"results_{run_id}.csv"
        
        try:
            results = self.get_test_results(run_id)
            if results:
                df = pd.DataFrame(results)
                df.to_csv(output_path, index=False)
                logger.info(f"Results exported to CSV: {output_path}")
                return output_path
            else:
                logger.warning(f"No results found for run: {run_id}")
                return None
        
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics
        """
        stats = {
            'data_directory_size': 0,
            'backup_directory_size': 0,
            'database_size': 0,
            'total_files': 0,
            'backup_count': 0
        }
        
        try:
            # Calculate directory sizes
            for directory, key in [(self.data_dir, 'data_directory_size'), 
                                  (self.backup_dir, 'backup_directory_size')]:
                if directory.exists():
                    total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
                    stats[key] = total_size
                    stats['total_files'] += len(list(directory.rglob('*')))
            
            # Calculate database size
            if self.database_url.startswith('sqlite'):
                db_path = Path(self.database_url.replace('sqlite:///', ''))
                if db_path.exists():
                    stats['database_size'] = db_path.stat().st_size
            
            # Count backups
            if self.backup_dir.exists():
                stats['backup_count'] = len([d for d in self.backup_dir.iterdir() if d.is_dir()])
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to calculate storage stats: {e}")
            return stats 