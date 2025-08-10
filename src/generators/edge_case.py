"""
Edge case test case generator for FailProof LLM.
"""

from typing import Dict, List, Any
from .base import BaseGenerator
from ..core.logger import get_logger
import random

logger = get_logger(__name__)


class EdgeCaseGenerator(BaseGenerator):
    """Generates edge case test cases."""
    
    def __init__(self):
        super().__init__(
            name="edge_case",
            description="Generates various edge cases like very small/large numbers, specific data formats, etc."
        )
    
    def generate(self, count: int = 1, **kwargs) -> List[Dict[str, Any]]:
        test_cases = []
        for i in range(count):
            # Example edge cases
            input_data = self._get_random_edge_case()
            test_cases.append(self._create_test_case(
                input_data=input_data,
                category="numeric_edge",
                name=f"numeric_edge_case_{self.generated_count + 1}",
                description=f"Test with numeric edge case: {input_data}",
                tags=["edge_case", "numeric"]
            ))
        logger.info(f"Generated {len(test_cases)} edge case test cases")
        return test_cases

    def _get_random_edge_case(self) -> str:
        edge_cases = [
            "0", "1", "-1", "1000000000", "-1000000000",
            "0.000000001", "999999999999.99999",
            "", # Empty string
            " ", # Whitespace string
            "\n", # Newline character
            "\t", # Tab character
            # Potential broken HTML/XML
            "<p>Broken HTML<span>",
            "<root><item>value</item><root>",
            # Mismatched CSV columns
            "col1,col2,col3\nval1,val2\nvalA,valB,valC,valD",
            # Weird Unicode
            "\u0000", # Null character
            "\u202E", # Right-to-left override
            "\uFEFF", # Zero width no-break space
            "\uD800\uDC00", # Surrogate pair (invalid if unpaired)
        ]
        return random.choice(edge_cases)

    def generate_specific_edge_case(self, case_type: str) -> Dict[str, Any]:
        if case_type == "empty_string":
            return self._create_test_case(
                input_data="",
                category="empty_input",
                name="empty_string_test",
                description="Test with an empty string input.",
                tags=["edge_case", "empty"]
            )
        elif case_type == "long_number":
            return self._create_test_case(
                input_data=str(10**50) + "." + str(10**50),
                category="numeric_extreme",
                name="very_long_number_test",
                description="Test with an extremely long numeric input.",
                tags=["edge_case", "numeric", "large_input"]
            )
        # Add more specific cases as needed
        else:
            raise ValueError(f"Unknown edge case type: {case_type}") 