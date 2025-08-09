"""
Adversarial test case generator for Stressor.
"""

import random
import json
import re
from typing import Dict, List, Any, Optional
from .base import BaseGenerator
from ..core.logger import get_logger

logger = get_logger(__name__)


class AdversarialGenerator(BaseGenerator):
    """Generates adversarial test cases for LLM stress testing."""
    
    def __init__(self):
        """Initialize the adversarial generator."""
        super().__init__(
            name="adversarial",
            description="Generates adversarial inputs including malformed JSON, typos, mixed languages, and edge cases"
        )
        
        # Malformed JSON templates
        self.malformed_json_templates = [
            '{"key": "value"',  # Missing closing brace
            '{"key": "value",}',  # Trailing comma
            '{"key": value}',  # Missing quotes
            '{"key": "value", "key2":}',  # Incomplete value
            '{"key": "value" "key2": "value2"}',  # Missing comma
            '[1, 2, 3,',  # Incomplete array
            '{"key": "value", "nested": {"key2": "value2"}',  # Unclosed nested
            '{"key": "value", "array": [1, 2, 3}',  # Unclosed array
        ]
        
        # Special characters and edge cases
        self.special_characters = [
            '!@#$%^&*()_+-=[]{}|;:,.<>?',
            '🚀🎯💡🔍⚡🎪🎨🎭🎪🎨',
            'Null null NULL',
            'undefined undefined',
            'NaN NaN',
            'Infinity -Infinity',
            '"" ""',
            "'' ''",
            '` `',
            '\\ \\',
            '// //',
            '<!-- -->',
            '<?php ?>',
            '<script></script>',
        ]
        
        # Mixed language examples
        self.mixed_languages = [
            "Hello 你好 Bonjour",
            "Testing 测试 Testen",
            "Error 错误 Erreur",
            "Success 成功 Erfolg",
            "Data 数据 Données",
        ]
        
        # Very long inputs
        self.long_input_templates = [
            "This is a very long input " * 1000,
            "A" * 10000,
            "Lorem ipsum " * 500,
            "Test case " * 2000,
        ]
        
        # Contradictory instructions
        self.contradictory_instructions = [
            "Tell me the truth but also lie to me",
            "Give me a short answer but also provide detailed explanations",
            "Be helpful but don't help me",
            "Respond quickly but take your time",
            "Be formal but also casual",
            "Give me numbers but don't use any numbers",
            "Be creative but follow strict rules",
        ]
    
    def generate(self, count: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate adversarial test cases.
        
        Args:
            count: Number of test cases to generate
            **kwargs: Additional generation parameters
            
        Returns:
            List of adversarial test cases
        """
        test_cases = []
        
        for i in range(count):
            # Choose a category for this test case
            category = self._choose_category()
            
            if category == "malformed_json":
                test_case = self._generate_malformed_json()
            elif category == "special_characters":
                test_case = self._generate_special_characters()
            elif category == "mixed_languages":
                test_case = self._generate_mixed_languages()
            elif category == "very_long":
                test_case = self._generate_very_long()
            elif category == "contradictory":
                test_case = self._generate_contradictory()
            elif category == "typos":
                test_case = self._generate_typos()
            elif category == "unicode":
                test_case = self._generate_unicode_edge_cases()
            else:
                test_case = self._generate_random_adversarial()
            
            test_cases.append(test_case)
        
        logger.info(f"Generated {len(test_cases)} adversarial test cases")
        return test_cases
    
    def _choose_category(self) -> str:
        """Choose a random category for test case generation."""
        categories = [
            "malformed_json",
            "special_characters", 
            "mixed_languages",
            "very_long",
            "contradictory",
            "typos",
            "unicode"
        ]
        return random.choice(categories)
    
    def _generate_malformed_json(self) -> Dict[str, Any]:
        """Generate malformed JSON test cases."""
        template = random.choice(self.malformed_json_templates)
        
        return self._create_test_case(
            input_data=template,
            category="malformed_json",
            name=f"malformed_json_{self.generated_count + 1}",
            description="Malformed JSON input that should cause parsing errors",
            expected_output="Error or graceful handling of malformed JSON",
            tags=["json", "parsing", "error_handling"],
            metadata={
                "json_type": "malformed",
                "template": template[:50] + "..." if len(template) > 50 else template
            }
        )
    
    def _generate_special_characters(self) -> Dict[str, Any]:
        """Generate test cases with special characters."""
        chars = random.choice(self.special_characters)
        
        return self._create_test_case(
            input_data=f"Process this input: {chars}",
            category="special_characters",
            name=f"special_chars_{self.generated_count + 1}",
            description="Input with special characters that might cause issues",
            expected_output="Proper handling of special characters",
            tags=["special_chars", "unicode", "edge_case"],
            metadata={
                "char_type": "special",
                "character_count": len(chars)
            }
        )
    
    def _generate_mixed_languages(self) -> Dict[str, Any]:
        """Generate test cases with mixed languages."""
        mixed_text = random.choice(self.mixed_languages)
        
        return self._create_test_case(
            input_data=f"Translate this: {mixed_text}",
            category="mixed_languages",
            name=f"mixed_languages_{self.generated_count + 1}",
            description="Input with mixed languages that might confuse the model",
            expected_output="Proper handling of mixed language input",
            tags=["multilingual", "language", "edge_case"],
            metadata={
                "languages": "mixed",
                "text_sample": mixed_text
            }
        )
    
    def _generate_very_long(self) -> Dict[str, Any]:
        """Generate very long input test cases."""
        long_input = random.choice(self.long_input_templates)
        
        return self._create_test_case(
            input_data=long_input,
            category="very_long",
            name=f"very_long_{self.generated_count + 1}",
            description="Very long input that might exceed model limits",
            expected_output="Proper handling of long inputs",
            tags=["long_input", "length_limit", "edge_case"],
            metadata={
                "input_length": len(long_input),
                "type": "repetitive_text"
            }
        )
    
    def _generate_contradictory(self) -> Dict[str, Any]:
        """Generate contradictory instruction test cases."""
        instruction = random.choice(self.contradictory_instructions)
        
        return self._create_test_case(
            input_data=instruction,
            category="contradictory",
            name=f"contradictory_{self.generated_count + 1}",
            description="Contradictory instructions that might confuse the model",
            expected_output="Graceful handling of contradictory instructions",
            tags=["contradiction", "instruction", "edge_case"],
            metadata={
                "instruction_type": "contradictory",
                "complexity": "high"
            }
        )
    
    def _generate_typos(self) -> Dict[str, Any]:
        """Generate test cases with intentional typos."""
        base_text = "This is a test case with intentional typos to check error handling"
        typo_text = self._add_typos(base_text, typo_rate=0.3)
        
        return self._create_test_case(
            input_data=typo_text,
            category="typos",
            name=f"typos_{self.generated_count + 1}",
            description="Input with intentional typos to test robustness",
            expected_output="Proper handling of text with typos",
            tags=["typos", "robustness", "error_handling"],
            metadata={
                "typo_rate": 0.3,
                "original_text": base_text
            }
        )
    
    def _generate_unicode_edge_cases(self) -> Dict[str, Any]:
        """Generate Unicode edge case test cases."""
        unicode_text = "Test with unicode: 你好世界 🚀🎯💡🔍⚡"
        mixed_unicode = self._add_unicode_variations(unicode_text)
        
        return self._create_test_case(
            input_data=mixed_unicode,
            category="unicode",
            name=f"unicode_{self.generated_count + 1}",
            description="Input with Unicode variations and edge cases",
            expected_output="Proper handling of Unicode characters",
            tags=["unicode", "internationalization", "edge_case"],
            metadata={
                "unicode_type": "mixed",
                "original_text": unicode_text
            }
        )
    
    def _generate_random_adversarial(self) -> Dict[str, Any]:
        """Generate a random adversarial test case."""
        # Combine multiple adversarial techniques
        base_input = "Test input for adversarial testing"
        
        # Add random variations
        variations = ["typo", "case", "unicode"]
        for variation in random.sample(variations, random.randint(1, len(variations))):
            base_input = self._add_variation(base_input, variation)
        
        # Add special characters randomly
        if random.random() < 0.5:
            base_input += " " + random.choice(self.special_characters)
        
        return self._create_test_case(
            input_data=base_input,
            category="random_adversarial",
            name=f"random_adversarial_{self.generated_count + 1}",
            description="Random combination of adversarial techniques",
            expected_output="Robust handling of combined adversarial inputs",
            tags=["adversarial", "combination", "edge_case"],
            metadata={
                "techniques_used": variations,
                "complexity": "high"
            }
        )
    
    def generate_specific_adversarial(self, category: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a specific type of adversarial test case.
        
        Args:
            category: Specific category to generate
            **kwargs: Category-specific parameters
            
        Returns:
            Adversarial test case
        """
        if category == "malformed_json":
            return self._generate_malformed_json()
        elif category == "special_characters":
            return self._generate_special_characters()
        elif category == "mixed_languages":
            return self._generate_mixed_languages()
        elif category == "very_long":
            return self._generate_very_long()
        elif category == "contradictory":
            return self._generate_contradictory()
        elif category == "typos":
            return self._generate_typos()
        elif category == "unicode":
            return self._generate_unicode_edge_cases()
        else:
            raise ValueError(f"Unknown adversarial category: {category}") 