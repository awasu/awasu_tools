""" Set up the awasu_tools module. """

from distutils.core import setup

# load the README
with open( "README.rst", "r", encoding="utf-8" ) as fp:
    readme = fp.read()

setup(
    name = "awasu-tools",
    version = "1.2",
    description = "Tools for writing Awasu extensions.",
    long_description = readme,
    url = "https://awasu.com/awasu_tools",
    author = "Awasu",
    author_email = "support@awasu.com",
    packages = [ "awasu_tools" ]
)
