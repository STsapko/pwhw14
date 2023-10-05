import os
import sys

sys.path.append((os.path.abspath("..")))

project = 'HW_14'
copyright = '2023, stsapko'
author = 'stsapko'

extensions = ["sphinx.ext.autodoc"]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'nature'
html_static_path = ['_static']
