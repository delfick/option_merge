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
with open(os.path.join(this_dir, "../conf.py")) as f:
    code = compile(f.read(), os.path.join(this_dir, "../conf.py"), 'exec')
    exec(code, globals(), locals())
