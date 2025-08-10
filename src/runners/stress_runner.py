"""
Stress runner for FailProof LLM.
"""

import asyncio
import time
from typing import Dict, List, Any
from datetime import datetime
from .base import BaseRunner
from ..core.logger import get_logger
import random

logger = get_logger(__name__)


class StressRunner(BaseRunner):
    """
    A runner designed for large-scale stress testing and performance measurement.
    This runner will focus on executing a high volume of test cases and collecting metrics.
    """
    
    def __init__(self, model_name: str = "generic-stress-model", **kwargs):
        super().__init__(model_name, **kwargs)
        self.successful_runs = 0
        self.failed_runs = 0
        self.total_latency_ms = 0
        logger.info(f"Initialized StressRunner for model: {self.model_name}")

    async def run_single_test(self, test_case: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Executes a single test case as part of a stress test.
        For a generic stress runner, this might involve a simple echo or a mocked API call.
        Actual LLM interaction would be delegated if this were a composite runner.
        """
        if not self._validate_test_case(test_case):
            self.failed_runs += 1
            return self._create_error_result(test_case, "Invalid test case structure")

        start_time = time.time()
        output_data = ""
        error_message = ""
        status = 'success'

        try:
            # Simulate a brief delay for processing
            await asyncio.sleep(0.01)
            
            # Simple echo for demonstration; in a real scenario, this would call an LLM
            output_data = f"Processed: {test_case['input_data'][:50]}..."
            
            # Simulate potential failures based on input content or randomness
            if "fail_me" in test_case['input_data'].lower():
                status = 'error'
                error_message = "Simulated failure due to keyword"
            elif random.random() < 0.05: # 5% chance of random failure
                status = 'error'
                error_message = "Simulated random processing error"

        except Exception as e:
            status = 'error'
            error_message = str(e)
            logger.error(f"Error in StressRunner for test case {test_case.get('test_id')}: {e}")

        finally:
            end_time = time.time()
            latency = self._calculate_latency(start_time, end_time)
            
            if status == 'success':
                self.successful_runs += 1
            else:
                self.failed_runs += 1
            self.total_latency_ms += latency

            return {
                'test_run_id': test_case.get('test_run_id', 'unknown'),
                'test_case_id': test_case.get('test_id', 'unknown'),
                'status': status,
                'input_data': test_case.get('input_data', ''),
                'output_data': output_data,
                'error_message': error_message,
                'latency': latency,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'model_name': self.model_name,
                    'runner': self.__class__.__name__,
                }
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get stress test statistics.
        """
        total_runs = self.successful_runs + self.failed_runs
        success_rate = (self.successful_runs / total_runs * 100) if total_runs > 0 else 0
        avg_latency = (self.total_latency_ms / total_runs) if total_runs > 0 else 0

        return {
            'total_tests': total_runs,
            'successful_tests': self.successful_runs,
            'failed_tests': self.failed_runs,
            'success_rate': success_rate,
            'average_latency': avg_latency
        }

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model (for StressRunner, this is generic).
        """
        return {
            'model_name': self.model_name,
            'provider': 'Generic',
            'runner_type': self.__class__.__name__,
            'supports_streaming': False,
            'supports_functions': False,
            'max_tokens': None
        } 