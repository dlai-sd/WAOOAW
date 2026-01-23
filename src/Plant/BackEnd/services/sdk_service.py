"""
SDK Service for generating client SDKs for the Plant API
"""

import os
import subprocess

class SDKService:
    """
    Service to handle the generation of client SDKs.
    """

    @staticmethod
    def generate_python_sdk():
        """
        Generate Python SDK and publish to internal PyPI.
        """
        # Command to generate Python SDK
        subprocess.run(["openapi-generator-cli", "generate", "-i", "http://localhost:8000/api/v1/openapi.json", "-g", "python", "-o", "python_sdk"])
        # Command to publish to internal PyPI
        subprocess.run(["twine", "upload", "python_sdk/*"])

    @staticmethod
    def generate_javascript_sdk():
        """
        Generate JavaScript SDK for frontend.
        """
        # Command to generate JavaScript SDK
        subprocess.run(["openapi-generator-cli", "generate", "-i", "http://localhost:8000/api/v1/openapi.json", "-g", "javascript", "-o", "javascript_sdk"])

