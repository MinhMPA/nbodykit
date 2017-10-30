# -*- coding: utf-8 -*-
#
# nbodykit documentation build configuration file, created by
# sphinx-quickstart on Thu Jul 30 14:47:26 2015.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.
import sys
import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

sys.path.insert(0, os.path.abspath('..'))
import nbodykit

from sphinx.ext.autosummary import Autosummary
from sphinx.ext.autosummary import get_documenter
from docutils.parsers.rst import directives
from sphinx.util.inspect import safe_getattr
import re

class AutoCosmoSummary(Autosummary):
    """
    Summarize all methods/attributes of the Cosmology class
    """
    exclude = ['dro', 'dro_dict', 'data']
    option_spec = {
        'methods': directives.unchanged,
        'attributes': directives.unchanged
    }
    required_arguments = 1

    @staticmethod
    def get_members(clazz, obj, typ):

        names = set()
        items = []

        # the default dir
        for name in dir(obj):
            try:
                documenter = get_documenter(safe_getattr(obj, name), obj)
            except AttributeError:
                continue
            if documenter.objtype == typ and not name.startswith('_'):
                if name not in AutoCosmoSummary.exclude:
                    items.append((clazz,name))
                    names.add(name) # keep track of method/attribute conflicts

        # the delegate dro
        for n in obj.dro:
            for name in dir(n):
                try:
                    documenter = get_documenter(safe_getattr(n, name), n)
                except AttributeError:
                    continue

                # dont do conflicts
                if name not in names:
                    if documenter.objtype == typ and not name.startswith('_'):
                        if name not in AutoCosmoSummary.exclude:
                            x = "%s.%s" %(n.__module__, n.__name__)
                            items.append((x,name))
                            names.add(name)

        return ['~%s.%s' %item for item in sorted(items, key=lambda x: x[1])]

    def run(self):
        clazz = str(self.arguments[0])
        try:
            (module_name, class_name) = clazz.rsplit('.', 1)
            m = __import__(module_name, globals(), locals(), [class_name])
            c = getattr(m, class_name)
            if 'methods' in self.options:
                self.content = self.get_members(clazz, c, 'method')
            if 'attributes' in self.options:
                self.content = self.get_members(clazz, c, 'attribute')
        finally:
            return super(AutoCosmoSummary, self).run()

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'nbsphinx',
    'numpydoc',
    'IPython.sphinxext.ipython_console_highlighting',
    'sphinx_issues',
]

# store the home directory for the docs
os.environ['NBKIT_DOCS'] = os.path.split(__file__)[0]

def autogen_modules():
    """
    Produce a file "modules.rst" that includes an ``autosummary`` directive
    listing all of the modules in nbodykit.

    The ``toctree`` option is set such that the corresponding rst files
    will be auto-generated in ``source/api/_autosummary``.
    """
    # current directory
    cur_dir = os.path.abspath(os.path.dirname(__file__))

    # top-level path of source tree
    toplevel = os.path.join(cur_dir, "..", '..')

    # where to dump the list of modules
    output_path = os.path.join(cur_dir, 'api')

    # directories and modules to ignore
    exclude_dirs = ['tests', 'extern', 'style']
    exclude_modules = ['cosmology.py', '__init__.py']

    # the list of modules
    modules = []

    # walk the tree structure
    module_dir = os.path.join(toplevel, 'nbodykit')
    for dirpath, dirs, filenames in os.walk(module_dir):

        # do not walk excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # add module with __init__.py
        if '__init__.py' in filenames:
            relpath = os.path.relpath(dirpath, toplevel)
            modules.append(relpath.replace(os.path.sep, '.'))

        # keep track of modules ending in .py
        for f in filenames:

            # module needs to end with .py
            if f.endswith('.py') and f not in exclude_modules:
                path = os.path.join(dirpath, f)
                relpath = os.path.relpath(path, toplevel) # get path starting with nbodykit.X.X
                relpath = relpath.replace(os.path.sep, '.')[:-3] # replace slash with dot
                modules.append(relpath)

    # write the output modules file
    output_file = os.path.join(output_path, 'modules.rst')
    with open(output_file, 'w') as ff:
        header = "Modules"
        header += "\n" + "="*len(header) + "\n"
        header = ":orphan:\n\n" + header
        ff.write(header+".. autosummary::\n\t:toctree: _autosummary\n\t:template: module.rst\n\n")
        for module in modules:
            ff.write("\t" + module + "\n")

        # separately add in the cosmology.py module with custom template
        ff.write("\n.. autosummary::\n\t:toctree: _autosummary\n\t:template: cosmo-module.rst\n\n")
        ff.write("\tnbodykit.cosmology.cosmology\n")

def autogen_lab_module():
    """
    Automatically generate the list of functions, classes, and modules imported
    into the :mod:`nbodykit.lab`module.

    This saves the list to ``source/api/_autosummary/nbodykit.lab.rst``.
    """
    import types
    from nbodykit import lab

    # all members of the lab module
    members = dir(lab)
    d = lab.__dict__

    # get all functions, modules, and classes
    trim = lambda typ: sorted([m for m in members if isinstance(d[m], typ)])
    modules = trim(types.ModuleType)
    classes = trim(types.ClassType)
    functions = trim(types.FunctionType)

    # the header
    out = "nbodykit.lab"
    out += "\n" + "="*len(out) + "\n\n"
    out += ".. automodule:: nbodykit.lab\n\n"
    out += "Below are the members of the nbodykit.lab module. We give the imported name of"
    out += " the member in this module and the full link in parentheses.\n\n"

    # output the list
    roles = [':mod:', ':class:', ':func:']
    all_members = [modules, classes, functions]
    names = ['Modules', 'Classes', 'Functions']
    for i, name in enumerate(names):
        members = all_members[i]
        if not len(members):
            continue
        out += ".. rubric:: %s\n\n" %name
        for member in members:
            val = d[member]
            name = ""
            if hasattr(val, '__module__'):
                name += val.__module__ + '.'
            name += val.__name__
            out += "- %s (%s`%s`)\n" % (member, roles[i], name)
        out += "\n"

    # the output path
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    toplevel = os.path.join(cur_dir, "..", '..')
    output_path = os.path.join(cur_dir, 'api', '_autosummary')
    output_file = os.path.join(output_path, 'nbodykit.lab.rst')

    # make the output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # and save
    with open(output_file, 'w') as ff:
        ff.write(out)

def setup(app):
    autogen_modules()
    autogen_lab_module()
    app.add_directive('autocosmosummary', AutoCosmoSummary)

# generate API rst files from autosummary command
autosummary_generate = True

# configure which methods show up
numpydoc_show_class_members = True
napoleon_include_special_with_doc = True
numpydoc_class_members_toctree = False

# link changelog to github
issues_github_path = 'bccp/nbodykit'


# document __init__ when it has a docstring
napoleon_include_init_with_doc = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = ['.rst']

html_sourcelink_suffix = ''

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'nbodykit'
copyright = u'2015-2017, Nick Hand, Yu Feng'
author = u'Nick Hand, Yu Feng'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The full version, including alpha/beta/rc tags.
release = nbodykit.__version__
if 'dev' in release:
    release = release.rsplit('.', 1)[0]+' - dev'

# Use release as the version.
version = release

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['build', '**.ipynb_checkpoints']

# The reST default role (used for this markup: `text`) to use for all
# documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
#keep_warnings = False

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

import sphinx_bootstrap_theme
html_theme = 'bootstrap'
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = dict(
    bootstrap_version = "3",
    bootswatch_theme = "readable",
    navbar_sidebarrel = False,
    globaltoc_depth = 2,
    navbar_links = [
    ("Cookbook", "cookbook/index"),
    ("API", "api/api")
    ],
)

#html_theme = 'nature'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_logo = '_static/nbodykit-logo-white.png'
# html_theme_options = {
#     'logo_only': True,
#     'display_version': False,
# }
# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = ""

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = ""

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
#html_extra_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Language to be used for generating the HTML full-text search index.
# Sphinx supports the following languages:
#   'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja'
#   'nl', 'no', 'pt', 'ro', 'ru', 'sv', 'tr'
#html_search_language = 'en'

# A dictionary with options for the search language support, empty by default.
# Now only 'ja' uses this config value
#html_search_options = {'type': 'default'}

# The name of a javascript file (relative to the configuration directory) that
# implements a search results scorer. If empty, the default will be used.
#html_search_scorer = 'scorer.js'

# Output file base name for HTML help builder.
htmlhelp_basename = 'nbodykitdoc'

html_show_sourcelink = True

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',

# Latex figure (float) alignment
#'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
  (master_doc, 'nbodykit.tex', u'nbodykit Documentation',
   author, 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'nbodykit', u'nbodykit Documentation',
     [author], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  (master_doc, 'nbodykit', u'nbodykit Documentation',
   author, 'nbodykit', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/2.7/', None),
    'pandas': ('http://pandas.pydata.org/pandas-docs/stable/', None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
    'xarray': ('http://xarray.pydata.org/en/stable/', None),
    'astropy': ('http://docs.astropy.org/en/stable/', None),
    'dask': ('http://dask.pydata.org/en/stable/', None),
    'halotools': ('https://halotools.readthedocs.io/en/stable/', None),
    'pmesh': ('http://rainwoodman.github.io/pmesh/', None),
    'Corrfunc': ('http://corrfunc.readthedocs.io/en/master/', None),
    'h5py': ('http://docs.h5py.org/en/stable/', None),
    'classylss': ('http://classylss.readthedocs.io/en/stable', None)
}
