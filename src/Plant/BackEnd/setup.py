from setuptools import setup, find_packages

setup(
    name="waooaw-plant-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.26.0",
    ],
    description="Python client SDK for WAOOAW Plant API",
    author="WAOOAW Team",
    author_email="team@waooaw.com",
    url="https://github.com/waooaw/plant-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
