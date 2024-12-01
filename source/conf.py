# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'Ecommerce Jad Ghamloush & Saadallah Itani'
copyright = '2024, Saad Itani , Jad Ghamloush'
author = 'Saad Itani , Jad Ghamloush'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',        # Automatically generates documentation from docstrings
    'sphinx.ext.napoleon',       # Supports Google-style and NumPy-style docstrings
    'sphinx.ext.viewcode',       # Adds links to the source code
]

templates_path = ['_templates']
exclude_patterns = []

# -- Add the project root directory to the system path -----------------------
import os
import sys
sys.path.insert(0, os.path.abspath('../service1'))
sys.path.insert(0, os.path.abspath('../service2'))
sys.path.insert(0, os.path.abspath('../service3'))
sys.path.insert(0, os.path.abspath('../service4'))
# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']
