from distutils.core import setup

setup( 
    name = "awasu-tools" ,
    version = "1.0.1" ,
    description = "Tools for writing Awasu extensions." ,
    long_description = open("README.rst","r").read() ,
    url = "http://awasu.com/awasu_tools" ,
    author = "Awasu" ,
    author_email = "support@awasu.com" ,
    packages = ["awasu_tools"]
)
