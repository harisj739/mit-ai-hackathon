"""
Base generator class for test cases.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.logger import get_logger

logger = get_logger(__name__)


class BaseGenerator(ABC):
    """Base class for all test case generators."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base generator.
        
        Args:
            name: Generator name
            description: Generator description
        """
        self.name = name
        self.description = description
        self.generated_count = 0
        logger.debug(f"Initialized generator: {name}")
    
    @abstractmethod
    def generate(self, count: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """
        Generate test cases.
        
        Args:
            count: Number of test cases to generate
            **kwargs: Additional generation parameters
            
        Returns:
            List of test case dictionaries
        """
        pass
    
    def _create_test_case(self, 
                         input_data: str, 
                         category: str,
                         name: str = None,
                         description: str = None,
                         expected_output: str = None,
                         tags: List[str] = None,
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a standardized test case structure.
        
        Args:
            input_data: Input data for the test case
            category: Test case category
            name: Test case name
            description: Test case description
            expected_output: Expected output
            tags: Tags for the test case
            metadata: Additional metadata
            
        Returns:
            Test case dictionary
        """
        test_id = str(uuid.uuid4())
        
        if name is None:
            name = f"{self.name}_{category}_{self.generated_count + 1}"
        
        if tags is None:
            tags = []
        
        if metadata is None:
            metadata = {}
        
        test_case = {
            'test_id': test_id,
            'category': category,
            'name': name,
            'description': description or f"Generated {category} test case by {self.name}",
            'input_data': input_data,
            'expected_output': expected_output,
            'tags': tags + [self.name, category],
            'metadata': {
                'generator': self.name,
                'generated_at': datetime.utcnow().isoformat(),
                'generation_count': self.generated_count + 1,
                **metadata
            }
        }
        
        self.generated_count += 1
        return test_case
    
    def _add_variation(self, base_input: str, variation_type: str, **kwargs) -> str:
        """
        Add variation to base input.
        
        Args:
            base_input: Base input string
            variation_type: Type of variation to apply
            **kwargs: Variation specific parameters
            
        Returns:
            Modified input string
        """
        if variation_type == "typo":
            return self._add_typos(base_input, **kwargs)
        elif variation_type == "case":
            return self._add_case_variations(base_input, **kwargs)
        elif variation_type == "unicode":
            return self._add_unicode_variations(base_input, **kwargs)
        else:
            return base_input
    
    def _add_typos(self, text: str, typo_rate: float = 0.1) -> str:
        """
        Add typos to text.
        
        Args:
            text: Input text
            typo_rate: Rate of typos to add (0-1)
            
        Returns:
            Text with typos
        """
        import random
        
        if typo_rate <= 0:
            return text
        
        words = text.split()
        for i in range(len(words)):
            if random.random() < typo_rate:
                word = words[i]
                if len(word) > 3:
                    # Simple typo simulation
                    typo_types = ['swap', 'replace', 'insert', 'delete']
                    typo_type = random.choice(typo_types)
                    
                    if typo_type == 'swap' and len(word) > 1:
                        # Swap adjacent characters
                        pos = random.randint(0, len(word) - 2)
                        chars = list(word)
                        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
                        words[i] = ''.join(chars)
                    
                    elif typo_type == 'replace' and len(word) > 1:
                        # Replace a character
                        pos = random.randint(0, len(word) - 1)
                        chars = list(word)
                        chars[pos] = random.choice('abcdefghijklmnopqrstuvwxyz')
                        words[i] = ''.join(chars)
                    
                    elif typo_type == 'insert':
                        # Insert a character
                        pos = random.randint(0, len(word))
                        chars = list(word)
                        chars.insert(pos, random.choice('abcdefghijklmnopqrstuvwxyz'))
                        words[i] = ''.join(chars)
                    
                    elif typo_type == 'delete' and len(word) > 1:
                        # Delete a character
                        pos = random.randint(0, len(word) - 1)
                        chars = list(word)
                        del chars[pos]
                        words[i] = ''.join(chars)
        
        return ' '.join(words)
    
    def _add_case_variations(self, text: str, variation_type: str = "random") -> str:
        """
        Add case variations to text.
        
        Args:
            text: Input text
            variation_type: Type of case variation
            
        Returns:
            Text with case variations
        """
        if variation_type == "upper":
            return text.upper()
        elif variation_type == "lower":
            return text.lower()
        elif variation_type == "title":
            return text.title()
        elif variation_type == "random":
            import random
            result = []
            for char in text:
                if random.random() < 0.5:
                    result.append(char.upper())
                else:
                    result.append(char.lower())
            return ''.join(result)
        else:
            return text
    
    def _add_unicode_variations(self, text: str) -> str:
        """
        Add Unicode variations to text.
        
        Args:
            text: Input text
            
        Returns:
            Text with Unicode variations
        """
        # Add some common Unicode variations
        unicode_variations = {
            'a': ['à', 'á', 'â', 'ã', 'ä', 'å'],
            'e': ['è', 'é', 'ê', 'ë'],
            'i': ['ì', 'í', 'î', 'ï'],
            'o': ['ò', 'ó', 'ô', 'õ', 'ö'],
            'u': ['ù', 'ú', 'û', 'ü'],
            'n': ['ñ'],
            'c': ['ç']
        }
        
        import random
        result = []
        for char in text.lower():
            if char in unicode_variations and random.random() < 0.3:
                result.append(random.choice(unicode_variations[char]))
            else:
                result.append(char)
        
        return ''.join(result)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get generator statistics.
        
        Returns:
            Generator statistics
        """
        return {
            'name': self.name,
            'description': self.description,
            'generated_count': self.generated_count,
            'type': self.__class__.__name__
        } 