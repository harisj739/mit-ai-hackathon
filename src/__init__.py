"""
Stressor - Stress-testing Framework for AI Systems

Description: A comprehensive stress-testing framework that bombards LLMs and AI agents
with edge cases, malformed inputs, and adversarial scenarios to identify
vulnerabilities and improve robustness.

Authors: Haris Jilani & Hamza Khan

Date: 2025-08-09

Version: 0.1.0
"""

from .core.config import Settings
from .core.logger import setup_logging

# Initialize logging
setup_logging()

# Export main components
__all__ = [
    "Settings",
    "setup_logging",
] 