# setup.py
from setuptools import setup, find_packages

setup(
    name="metabarcoding_taxonomy",
    version="1.0.0",
    description="메타바코딩 분류군 분석 패키지",
    author="Seokwoo JO",
    author_email="newgenes1031@gmail.com",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "pandas",
        "numpy", 
        "matplotlib"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)