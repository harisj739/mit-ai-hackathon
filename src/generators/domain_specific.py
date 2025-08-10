"""
Domain-specific test case generator for FailProof LLM.
"""

from typing import Dict, List, Any
from .base import BaseGenerator
from ..core.logger import get_logger

logger = get_logger(__name__)


class DomainSpecificGenerator(BaseGenerator):
    """Generates domain-specific test cases relevant to chosen industries."""
    
    def __init__(self):
        super().__init__(
            name="domain_specific",
            description="Generates scenarios relevant to chosen industries (e.g., healthcare codes, legal clauses, financial data formatting)."
        )
        self.healthcare_codes = [
            "ICD-10: I10", "CPT: 99213", "HCPCS: J0897",
            "Invalid ICD: X99", "Malformed CPT: 1234",
        ]
        self.legal_clauses = [
            "Notwithstanding anything to the contrary herein",
            "Force majeure event shall mean",
            "This agreement is governed by the laws of",
            "Clause 3.1.2 states that the party shall be indemnified against all losses",
            "This contract is null and voidable upon breach of terms",
        ]
        self.financial_data = [
            "USD 1,234.56", "EUR 987,65", "JPY 10000",
            "Currency: USD Amount: 1,000.00 Date: 2023-13-40", # Malformed date
            "Transaction ID: ABC-123 Amount: $1,000.00 USD Status: Pending",
        ]

    def generate(self, count: int = 1, domain: str = "healthcare", **kwargs) -> List[Dict[str, Any]]:
        test_cases = []
        for i in range(count):
            if domain == "healthcare":
                input_data = self._get_random_healthcare_case()
                category = "healthcare_domain"
            elif domain == "legal":
                input_data = self._get_random_legal_case()
                category = "legal_domain"
            elif domain == "financial":
                input_data = self._get_random_financial_case()
                category = "financial_domain"
            else:
                raise ValueError(f"Unknown domain: {domain}")
            
            test_cases.append(self._create_test_case(
                input_data=input_data,
                category=category,
                name=f"{domain}_case_{self.generated_count + 1}",
                description=f"Test with {domain} specific edge case: {input_data}",
                tags=["domain_specific", domain]
            ))
        logger.info(f"Generated {len(test_cases)} {domain} domain-specific test cases")
        return test_cases

    def _get_random_healthcare_case(self) -> str:
        import random
        return random.choice(self.healthcare_codes)

    def _get_random_legal_case(self) -> str:
        import random
        return random.choice(self.legal_clauses)

    def _get_random_financial_case(self) -> str:
        import random
        return random.choice(self.financial_data)

    def generate_specific_domain_case(self, domain: str, case_type: str) -> Dict[str, Any]:
        # Implement logic for specific case types within a domain if needed
        if domain == "healthcare" and case_type == "invalid_icd":
            return self._create_test_case(
                input_data="ICD-10: Z99.99 (invalid code)",
                category="healthcare_invalid_code",
                name="invalid_icd_test",
                description="Test with an invalid ICD-10 code.",
                tags=["domain_specific", "healthcare", "validation_error"]
            )
        else:
            raise ValueError(f"Unknown domain-specific case type: {case_type} for domain {domain}") 