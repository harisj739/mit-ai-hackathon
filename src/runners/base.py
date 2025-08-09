"""
Base runner class for LLM testing.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
from ..core.logger import get_logger
from ..core.storage import StorageManager

logger = get_logger(__name__)


class BaseRunner(ABC):
    """Base class for all LLM test runners."""
    
    def __init__(self, model_name: str, storage_manager: StorageManager = None):
        """
        Initialize the base runner.
        
        Args:
            model_name: Name of the model to test
            storage_manager: Storage manager instance
        """
        self.model_name = model_name
        self.storage_manager = storage_manager or StorageManager()
        self.results = []
        self.error_count = 0
        self.success_count = 0
        self.total_latency = 0
        
        logger.info(f"Initialized {self.__class__.__name__} for model: {model_name}")
    
    @abstractmethod
    async def run_single_test(self, test_case: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Run a single test case.
        
        Args:
            test_case: Test case to run
            **kwargs: Additional parameters
            
        Returns:
            Test result dictionary
        """
        pass
    
    async def run_test_batch(self, test_cases: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Run a batch of test cases.
        
        Args:
            test_cases: List of test cases to run
            **kwargs: Additional parameters
            
        Returns:
            List of test results
        """
        results = []
        
        for test_case in test_cases:
            try:
                result = await self.run_single_test(test_case, **kwargs)
                results.append(result)
                
                # Update counters
                if result.get('status') == 'success':
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Update latency
                self.total_latency += result.get('latency', 0)
                
            except Exception as e:
                logger.error(f"Error running test case {test_case.get('test_id', 'unknown')}: {e}")
                
                # Create error result
                error_result = self._create_error_result(test_case, str(e))
                results.append(error_result)
                self.error_count += 1
        
        return results
    
    async def run_concurrent_tests(self, test_cases: List[Dict[str, Any]], max_concurrent: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Run test cases concurrently.
        
        Args:
            test_cases: List of test cases to run
            max_concurrent: Maximum number of concurrent tests
            **kwargs: Additional parameters
            
        Returns:
            List of test results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def run_with_semaphore(test_case):
            async with semaphore:
                return await self.run_single_test(test_case, **kwargs)
        
        # Create tasks
        tasks = [run_with_semaphore(test_case) for test_case in test_cases]
        
        # Run concurrently and collect results
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                
                # Update counters
                if result.get('status') == 'success':
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Update latency
                self.total_latency += result.get('latency', 0)
                
            except Exception as e:
                logger.error(f"Error in concurrent test execution: {e}")
                # Create error result for failed task
                error_result = self._create_error_result({}, str(e))
                results.append(error_result)
                self.error_count += 1
        
        return results
    
    def _create_error_result(self, test_case: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        Create an error result for a failed test case.
        
        Args:
            test_case: Original test case
            error_message: Error message
            
        Returns:
            Error result dictionary
        """
        return {
            'test_run_id': test_case.get('test_run_id', 'unknown'),
            'test_case_id': test_case.get('test_id', 'unknown'),
            'status': 'error',
            'input_data': test_case.get('input_data', ''),
            'output_data': '',
            'error_message': error_message,
            'latency': 0,
            'created_at': datetime.utcnow().isoformat(),
            'metadata': {
                'error_type': 'execution_error',
                'runner': self.__class__.__name__
            }
        }
    
    def _calculate_latency(self, start_time: float, end_time: float) -> int:
        """
        Calculate latency in milliseconds.
        
        Args:
            start_time: Start time
            end_time: End time
            
        Returns:
            Latency in milliseconds
        """
        return int((end_time - start_time) * 1000)
    
    def _validate_test_case(self, test_case: Dict[str, Any]) -> bool:
        """
        Validate a test case before running.
        
        Args:
            test_case: Test case to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['test_id', 'input_data']
        
        for field in required_fields:
            if field not in test_case:
                logger.warning(f"Test case missing required field: {field}")
                return False
        
        if not test_case.get('input_data'):
            logger.warning(f"Test case {test_case.get('test_id')} has empty input_data")
            return False
        
        return True
    
    def _sanitize_input(self, input_data: str) -> str:
        """
        Sanitize input data before sending to model.
        
        Args:
            input_data: Input data to sanitize
            
        Returns:
            Sanitized input data
        """
        # Basic sanitization - can be extended based on needs
        if isinstance(input_data, str):
            # Remove null bytes and other problematic characters
            sanitized = input_data.replace('\x00', '').strip()
            return sanitized
        return str(input_data)
    
    def save_results(self, results: List[Dict[str, Any]], run_id: str = None) -> str:
        """
        Save test results to storage.
        
        Args:
            results: Test results to save
            run_id: Test run ID (auto-generated if not provided)
            
        Returns:
            Test run ID
        """
        if not run_id:
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.model_name}"
        
        try:
            # Save test run metadata
            run_data = {
                'run_id': run_id,
                'model_name': self.model_name,
                'status': 'completed',
                'config': {
                    'runner': self.__class__.__name__,
                    'model_name': self.model_name
                },
                'results': {
                    'total_tests': len(results),
                    'success_count': self.success_count,
                    'error_count': self.error_count,
                    'average_latency': self.total_latency / len(results) if results else 0
                },
                'metadata': {
                    'created_at': datetime.utcnow().isoformat(),
                    'runner_type': self.__class__.__name__
                }
            }
            
            # Save test run
            self.storage_manager.save_test_run(run_data)
            
            # Save individual results
            for result in results:
                result['test_run_id'] = run_id
                self.storage_manager.save_test_result(result)
            
            logger.info(f"Saved {len(results)} test results for run: {run_id}")
            return run_id
        
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get runner statistics.
        
        Returns:
            Runner statistics
        """
        total_tests = self.success_count + self.error_count
        
        return {
            'model_name': self.model_name,
            'total_tests': total_tests,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': (self.success_count / total_tests * 100) if total_tests > 0 else 0,
            'average_latency': (self.total_latency / total_tests) if total_tests > 0 else 0,
            'runner_type': self.__class__.__name__
        }
    
    def reset_stats(self):
        """Reset runner statistics."""
        self.results = []
        self.error_count = 0
        self.success_count = 0
        self.total_latency = 0
        logger.debug("Reset runner statistics") 