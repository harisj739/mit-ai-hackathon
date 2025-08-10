"""
OpenAI API runner for Stressor. 
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from openai import AsyncOpenAI
from .base import BaseRunner
from ..core.config import settings
from ..core.logger import get_logger

logger = get_logger(__name__)


class OpenAIRunner(BaseRunner):
    """Runner for OpenAI models."""
    
    def __init__(self, model_name: str = None, api_key: str = None, **kwargs):
        """
        Initialize the OpenAI runner.
        
        Args:
            model_name: OpenAI model name (e.g., 'gpt-5')
            api_key: OpenAI API key
            **kwargs: Additional arguments
        """
        self.model_name = model_name or settings.default_model
        
        # Initialize OpenAI client
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        elif settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError("OpenAI API key must be provided either directly or via settings")
        
        super().__init__(self.model_name, **kwargs)
        
        logger.info(f"Initialized OpenAI runner for model: {self.model_name}")
    
    async def run_single_test(self, test_case: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Run a single test case against OpenAI model.
        
        Args:
            test_case: Test case to run
            **kwargs: Additional parameters
            
        Returns:
            Test result dictionary
        """
        if not self._validate_test_case(test_case):
            return self._create_error_result(test_case, "Invalid test case")
        
        start_time = time.time()
        
        try:
            # Prepare input data
            input_data = self._sanitize_input(test_case['input_data'])
            
            # Prepare messages
            messages = self._prepare_messages(input_data, **kwargs)
            
            # Prepare API parameters
            params = self._prepare_api_params(**kwargs)
            
            # Make API call
            response = await self._make_api_call(messages, params)
            
            end_time = time.time()
            latency = self._calculate_latency(start_time, end_time)
            
            # Process response
            result = self._process_response(response, test_case, latency)
            
            return result
        
        except Exception as e:
            end_time = time.time()
            latency = self._calculate_latency(start_time, end_time)
            
            logger.error(f"OpenAI API error for test case {test_case.get('test_id')}: {e}")
            return self._create_error_result(test_case, str(e))
    
    def _prepare_messages(self, input_data: str, **kwargs) -> List[Dict[str, str]]:
        """
        Prepare messages for OpenAI API.
        
        Args:
            input_data: Input data
            **kwargs: Additional parameters
            
        Returns:
            List of messages
        """
        messages = []
        
        # Add system message if provided
        system_message = kwargs.get('system_message', 'You are a helpful AI assistant.')
        if system_message:
            messages.append({
                'role': 'system',
                'content': system_message
            })
        
        # Add user message
        messages.append({
            'role': 'user',
            'content': input_data
        })
        
        return messages
    
    def _prepare_api_params(self, **kwargs) -> Dict[str, Any]:
        """
        Prepare API parameters for OpenAI call.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            API parameters dictionary
        """
        params = {
            'model': self.model_name,
            'max_tokens': kwargs.get('max_tokens', settings.default_max_tokens),
            'temperature': kwargs.get('temperature', settings.default_temperature),
        }
        
        # Add optional parameters
        optional_params = ['top_p', 'frequency_penalty', 'presence_penalty', 'stop']
        for param in optional_params:
            if param in kwargs:
                params[param] = kwargs[param]
        
        return params
    
    async def _make_api_call(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> Any:
        """
        Make API call to OpenAI.
        
        Args:
            messages: Messages to send
            params: API parameters
            
        Returns:
            OpenAI response
        """
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
                **params
            )
            return response
        
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            # Wait and retry
            await asyncio.sleep(60)
            return await self._make_api_call(messages, params)
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _process_response(self, response: Any, test_case: Dict[str, Any], latency: int) -> Dict[str, Any]:
        """
        Process OpenAI response.
        
        Args:
            response: OpenAI response
            test_case: Original test case
            latency: Response latency
            
        Returns:
            Processed result
        """
        try:
            # Extract content from response
            content = response.choices[0].message.content if response.choices else ""
            
            # Determine status based on response
            status = 'success'
            error_message = ""
            
            # Check for common error indicators
            if not content:
                status = 'error'
                error_message = "Empty response from model"
            elif "error" in content.lower() or "sorry" in content.lower():
                # This might indicate a refusal or error response
                status = 'refusal'
                error_message = "Model refused or provided error response"
            
            result = {
                'test_run_id': test_case.get('test_run_id', 'unknown'),
                'test_case_id': test_case.get('test_id', 'unknown'),
                'status': status,
                'input_data': test_case.get('input_data', ''),
                'output_data': content,
                'error_message': error_message,
                'latency': latency,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'model_name': self.model_name,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                        'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                        'total_tokens': response.usage.total_tokens if response.usage else 0
                    },
                    'finish_reason': response.choices[0].finish_reason if response.choices else None,
                    'runner': self.__class__.__name__
                }
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {e}")
            return self._create_error_result(test_case, f"Response processing error: {e}")
    
    async def run_with_retry(self, test_case: Dict[str, Any], max_retries: int = 3, **kwargs) -> Dict[str, Any]:
        """
        Run test case with retry logic.
        
        Args:
            test_case: Test case to run
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
            
        Returns:
            Test result
        """
        for attempt in range(max_retries):
            try:
                result = await self.run_single_test(test_case, **kwargs)
                
                # If successful, return immediately
                if result.get('status') == 'success':
                    return result
                
                # If it's a rate limit error, wait and retry
                if 'rate limit' in result.get('error_message', '').lower():
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue
                
                # For other errors, return the result
                return result
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return self._create_error_result(test_case, f"All retries failed: {e}")
                
                # Wait before retry
                await asyncio.sleep(1)
        
        return self._create_error_result(test_case, "Max retries exceeded")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Model information
        """
        return {
            'model_name': self.model_name,
            'provider': 'OpenAI',
            'runner_type': self.__class__.__name__,
            'supports_streaming': True,
            'supports_functions': True,
            'max_tokens': settings.default_max_tokens
        } 