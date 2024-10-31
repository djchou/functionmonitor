# setup.py
from setuptools import setup, find_packages

# Read in the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="functionmonitor",                     # The package name
    version="0.1.7",                            # Initial version number
    description="A tool for monitoring and managing asynchronous function execution.",
    long_description=long_description,          # Use the README as the long description
    long_description_content_type="text/markdown",  # Specify Markdown format for PyPI
    author="Dennis Chou",                       # Your name
    author_email="dennischou@gmail.com",        # Your email
    url="https://github.com/djchou/functionmonitor",  # URL to your repository
    packages=find_packages(),                   # Automatically find sub-packages
    install_requires=[                          # Dependencies
        "IPython",                              # Add any other dependencies
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
