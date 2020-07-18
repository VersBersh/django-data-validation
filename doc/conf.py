from PSphinxTheme.utils import set_psphinxtheme


html_theme_path, html_theme, needs_sphinx = set_psphinxtheme("p-main_theme")


# -- Project information -----------------------------------------------------

project = "Django Data Validation"
copyright = "2020, Oliver Chambers"  # noqa
author = "Oliver Chambers"
release = "0.0.1-alpha"


# -- General configuration ---------------------------------------------------

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_static_path = ["_static"]
templates_path = ["_templates"]

html_style = "ddv.css"
