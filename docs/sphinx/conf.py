"""
    Options for sphinx
    Add project specific options to conf.py in the root folder
"""
import sys, os
import sphinx_rtd_theme

this_dir = os.path.abspath(os.path.dirname(__file__))

extensions = ['sphinx.ext.autodoc']

html_theme = 'the_theme'
html_theme_path = [os.path.join(this_dir, 'templates'), sphinx_rtd_theme.get_html_theme_path()]
html_static_path = [os.path.join(this_dir, "static")]

exclude_patterns = ["_build/**", "venv/**"]

master_doc = 'index'
source_suffix = '.rst'

pygments_style = 'pastie'

# Add options specific to this project
execfile(os.path.join(this_dir, '../conf.py'), globals(), locals())
