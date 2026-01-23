"""
SDK Service for generating client SDKs for the WAOOAW Plant API.
"""

import os
import subprocess

class SDKService:
    """
    Service to handle SDK generation for Python and JavaScript clients.
    """

    @staticmethod
    def generate_python_sdk():
        """
        Generate Python SDK and publish to internal PyPI.
        """
        # Command to generate Python SDK
        subprocess.run(["openapi-generator-cli", "generate", 
                        "-i", "http://localhost:8000/api/v1/openapi.json", 
                        "-g", "python", 
                        "-o", "python_sdk"], check=True)
        # Publish to internal PyPI
        subprocess.run(["twine", "upload", "python_sdk/*"], check=True)

    @staticmethod
    def generate_javascript_sdk():
        """
        Generate JavaScript SDK for frontend.
        """
        # Command to generate JavaScript SDK
        subprocess.run(["openapi-generator-cli", "generate", 
                        "-i", "http://localhost:8000/api/v1/openapi.json", 
                        "-g", "javascript", 
                        "-o", "javascript_sdk"], check=True)

# Example usage
if __name__ == "__main__":
    SDKService.generate_python_sdk()
    SDKService.generate_javascript_sdk()
