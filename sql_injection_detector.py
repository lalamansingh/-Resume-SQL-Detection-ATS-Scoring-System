import re
import logging
from typing import Tuple, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLInjectionDetector:
    def __init__(self):
        # Define regex patterns for common SQL injection attempts
        # Case-insensitive
        self.patterns = [
            # Union-based injection
            r'(\bUNION\b\s+\bSELECT\b)',
            # Tautology-based injection
            r"(\bOR\b\s*['\"']?\w+['\"']?\s*=\s*['\"']?\w+['\"']?)",
            # Comment-based injection to terminate queries
            r'(--|\#|/\*.*?\*/)',
            # Stacked queries
            r'(\b;\s*(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)',
            # Union with select all columns
            r'(\bUNION\b\s+\bALL\b\s+\bSELECT\b)',
            # Common SQL keywords in suspicious contexts
            r'(\bSELECT\b\s+\*\s+\bFROM\b)',
            r'(\bDROP\b\s+\bTABLE\b)',
            r'(\bDELETE\b\s+\bFROM\b)',
            r'(\bINSERT\b\s+\bINTO\b)',
            r'(\bUPDATE\b\s+\bSET\b)',
            # Potential blind injection
            r'(\bSLEEP\b\s*\(\s*\d+\s*\))',
            r'(\bBENCHMARK\b\s*\()',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns]
        # Whitelist of safe phrases that might appear in resumes (to reduce false positives)
        self.whitelist = [
            r'experience\s+with\s+sql',
            r'sql\s+server',
            r'mysql',
            r'oracle\s+database',
            r'pl\/sql',
            r'tsql',
            r'database\s+administration',
            r'data\s+analysis',
            r'structured\s+query\s+language',
        ]
        self.whitelist_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.whitelist]

    def detect(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect SQL injection attempts in text.
        Returns a tuple (is_malicious, list_of_matches)
        """
        matches = []
        for pattern in self.compiled_patterns:
            found = pattern.findall(text)
            if found:
                matches.extend(found if isinstance(found[0], str) else [x[0] if isinstance(x, tuple) else x for x in found])

        # Filter out matches that are part of whitelist phrases
        filtered_matches = []
        for match in matches:
            # Check if the match is within a whitelist context
            is_safe = False
            for w_pattern in self.whitelist_patterns:
                if w_pattern.search(text):
                    # If the whitelist pattern is found in the text, we assume the match is safe
                    # This is a simplistic approach; in reality, we'd need to check proximity
                    is_safe = True
                    break
            if not is_safe:
                filtered_matches.append(match)

        is_malicious = len(filtered_matches) > 0
        logger.info(f"SQL injection detection: {is_malicious}, matches: {filtered_matches}")
        return is_malicious, filtered_matches

    def sanitize(self, text: str) -> str:
        """
        Remove detected SQL injection patterns from text.
        Returns sanitized text.
        """
        sanitized = text
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub('', sanitized)
        # Optionally, we could also remove extra whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        logger.info("Text sanitized for SQL injection patterns.")
        return sanitized

    def detect_and_sanitize(self, text: str) -> Tuple[bool, str, List[str]]:
        """
        Detect SQL injection and return sanitized text.
        Returns (is_malicious, sanitized_text, matches)
        """
        is_malicious, matches = self.detect(text)
        sanitized = self.sanitize(text) if is_malicious else text
        return is_malicious, sanitized, matches

if __name__ == "__main__":
    # Example usage
    detector = SQLInjectionDetector()
    test_texts = [
        "Experienced in SQL Server administration and database design.",
        "'; DROP TABLE users; --",
        "OR '1'='1'",
        "SELECT * FROM employees WHERE salary > 50000",
        "Proficient in PL/SQL and Oracle development."
    ]
    for text in test_texts:
        is_malicious, sanitized, matches = detector.detect_and_sanitize(text)
        print(f"Original: {text}")
        print(f"Malicious: {is_malicious}")
        print(f"Sanitized: {sanitized}")
        print(f"Matches: {matches}")
        print("-" * 50)