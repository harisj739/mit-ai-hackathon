"""
Basic tests for Stressor framework.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.config import Settings
from core.storage import StorageManager
from generators import AdversarialGenerator, PromptInjectionGenerator
from runners.base import BaseRunner


class TestConfig:
    """Test configuration management."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized."""
        settings = Settings()
        assert settings.model_name is not None
        assert settings.debug is not None
    
    def test_settings_validation(self):
        """Test settings validation."""
        with pytest.raises(ValueError):
            Settings(secret_key="short")  # Should fail validation


class TestGenerators:
    """Test test case generators."""
    
    def test_adversarial_generator(self):
        """Test adversarial generator."""
        generator = AdversarialGenerator()
        test_cases = generator.generate(5)
        
        assert len(test_cases) == 5
        assert all(isinstance(tc, dict) for tc in test_cases)
        assert all('test_id' in tc for tc in test_cases)
        assert all('input_data' in tc for tc in test_cases)
    
    def test_prompt_injection_generator(self):
        """Test prompt injection generator."""
        generator = PromptInjectionGenerator()
        test_cases = generator.generate(3)
        
        assert len(test_cases) == 3
        assert all(isinstance(tc, dict) for tc in test_cases)
        assert all('test_id' in tc for tc in test_cases)
        assert all('input_data' in tc for tc in test_cases)
    
    def test_generator_specific_categories(self):
        """Test generating specific categories."""
        adversarial_gen = AdversarialGenerator()
        test_case = adversarial_gen.generate_specific_adversarial("malformed_json")
        
        assert test_case['category'] == 'malformed_json'
        assert 'input_data' in test_case
    
    def test_generator_stats(self):
        """Test generator statistics."""
        generator = AdversarialGenerator()
        generator.generate(5)
        
        stats = generator.get_stats()
        assert stats['generated_count'] == 5
        assert stats['name'] == 'adversarial'


class TestStorage:
    """Test storage management."""
    
    def test_storage_initialization(self):
        """Test storage manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(database_url=f"sqlite:///{temp_dir}/test.db")
            assert storage is not None
    
    def test_storage_save_load(self):
        """Test saving and loading data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(database_url=f"sqlite:///{temp_dir}/test.db")
            
            # Test saving JSON data
            test_data = {"test": "data", "number": 42}
            file_path = storage.save_json_data("test.json", test_data, compress=False)
            
            assert file_path.exists()
            
            # Test loading JSON data
            loaded_data = storage.load_json_data("test.json", compress=False)
            assert loaded_data == test_data
    
    def test_storage_backup(self):
        """Test backup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(database_url=f"sqlite:///{temp_dir}/test.db")
            
            backup_path = storage.create_backup("test_backup")
            assert backup_path.exists()
            assert backup_path.is_dir()


class TestRunners:
    """Test test runners."""
    
    def test_runner_initialization(self):
        """Test runner initialization."""
        runner = Mock(spec=BaseRunner)
        assert runner is not None
    
    @pytest.mark.asyncio
    async def test_runner_validation(self):
        """Test test case validation."""
        # Create a mock runner
        class MockRunner(BaseRunner):
            async def run_single_test(self, test_case, **kwargs):
                return {"status": "success", "test_id": test_case.get('test_id')}
        
        runner = MockRunner("test-model")
        
        # Test valid test case
        valid_case = {"test_id": "test1", "input_data": "test input"}
        assert runner._validate_test_case(valid_case) is True
        
        # Test invalid test case
        invalid_case = {"test_id": "test2"}  # Missing input_data
        assert runner._validate_test_case(invalid_case) is False
    
    def test_runner_stats(self):
        """Test runner statistics."""
        class MockRunner(BaseRunner):
            async def run_single_test(self, test_case, **kwargs):
                return {"status": "success", "test_id": test_case.get('test_id')}
        
        runner = MockRunner("test-model")
        runner.success_count = 5
        runner.error_count = 2
        runner.total_latency = 1000
        
        stats = runner.get_stats()
        assert stats['total_tests'] == 7
        assert stats['success_rate'] == pytest.approx(71.43, rel=0.01)


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_generation(self):
        """Test end-to-end test case generation."""
        # Generate test cases
        adversarial_gen = AdversarialGenerator()
        injection_gen = PromptInjectionGenerator()
        
        adversarial_cases = adversarial_gen.generate(2)
        injection_cases = injection_gen.generate(2)
        
        all_cases = adversarial_cases + injection_cases
        
        assert len(all_cases) == 4
        assert all('test_id' in case for case in all_cases)
        assert all('input_data' in case for case in all_cases)
        
        # Test data persistence
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(database_url=f"sqlite:///{temp_dir}/test.db")
            
            # Save test cases
            file_path = storage.save_json_data("test_cases.json", all_cases, compress=False)
            assert file_path.exists()
            
            # Load test cases
            loaded_cases = storage.load_json_data("test_cases.json", compress=False)
            assert len(loaded_cases) == 4
            assert all_cases == loaded_cases
    
    def test_configuration_loading(self):
        """Test configuration loading from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = """
            model_name: gpt-3.5-turbo
            debug: true
            max_requests_per_minute: 30
            """
            f.write(config_data)
            config_path = f.name
        
        try:
            settings = Settings.load_from_file(config_path)
            assert settings.model_name == 'gpt-3.5-turbo'
            assert settings.debug is True
            assert settings.max_requests_per_minute == 30
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__]) 