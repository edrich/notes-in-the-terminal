#!/usr/bin/env python3
"""
Setup script for the Notes in the Terminal Application
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_file(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return ''

setup(
    name='notes-in-the-terminal',
    version='1.0.0',
    description='A terminal-based notes application with encryption support',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Notes CLI',
    python_requires='>=3.6',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'notes=notes_app.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Office/Business',
        'Topic :: Utilities',
    ],
    keywords='notes terminal cli encryption gpg productivity',
)
