"""
Setup script for ECS - Equation Calculation Sheet
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ecs-equation",
    version="1.0.0",
    author="ECS Team",
    author_email="ecs@example.com",
    description="ECS - Equation Calculation Sheet: A DSL for mathematical calculations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ecs-team/ecs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    keywords="math, equation, calculator, dsl, physics, engineering, scientific",
    project_urls={
        "Bug Reports": "https://github.com/ecs-team/ecs/issues",
        "Source": "https://github.com/ecs-team/ecs",
    },
)
