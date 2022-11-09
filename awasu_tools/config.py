""" Provide access to an Awasu config file. """

# COPYRIGHT:   (c) Awasu Pty. Ltd. 2015 (all rights reserved).
#              Unauthorized use of this code is prohibited.
#
# LICENSE:     This software is provided 'as-is', without any express
#              or implied warranty.
#
#              In no event will the author be held liable for any damages
#              arising from the use of this software.
#
#              Permission is granted to anyone to use this software
#              for any purpose, and to alter it and redistribute it freely,
#              subject to the following restrictions:
#
#              - The origin of this software must not be misrepresented;
#                you must not claim that you wrote the original software.
#                If you use this software, an acknowledgement is requested
#                but not required.
#
#              - Altered source versions must be plainly marked as such,
#                and must not be misrepresented as being the original software.
#                Altered source is encouraged to be submitted back to
#                the original author so it can be shared with the community.
#                Please share your changes.
#
#              - This notice may not be removed or altered from any
#                source distribution.

import sys
import os
import io
import re
import unittest

# ---------------------------------------------------------------------

class ConfigFile:
    """Provide access to an Awasu config file."""

    # TextVal types
    # nb: see https://awasu.com/forums/viewtopic.php?p=32904#p32904
    TVT_UNKNOWN = 0 # nb: Awasu doesn't know if the value is plain-text or HTML
    TVT_PLAINTEXT = 1
    TVT_HTML = 2

    def __init__( self, src ):
        """Load an Awasu config file."""
        # load the config file
        if os.path.isfile( src ):
            with open( src, "r", encoding="utf-8" ) as fp:
                buf = fp.read()
            self.filename = src
        elif isinstance( src, bytes ):
            buf = src.decode( "utf-8" )
            self.filename = None
        else:
            buf = str( src )
            self.filename = None
        if buf[0] == "\ufeff":
            buf = buf[1:] # nb: remove the BOM
        # NOTE: We can't use win32api.GetPrivateProfileXXX() since it barfs
        # on very long strings (~2K), so we parse the INI file manually :-/
        # However, we don't use ConfigParser, since we need full control
        # over how the file gets parsed.
        self.sections = {}
        curr_section_name = None
        for line_buf in io.StringIO( buf ):
            line_buf = line_buf.strip()
            if not line_buf or line_buf.startswith( ( "#", ";", "'" ) ):
                continue # nb: ignore comments and blank lines
            mo = re.search( r"^\[\s*([^]]+)\s*\]", line_buf )
            if mo:
                # found the start of a new section
                curr_section_name = mo.group(1).strip().lower()
                self.sections[ curr_section_name ] = {}
                continue
            mo = re.search( r"([^[=]+)\s*=", line_buf )
            if mo and curr_section_name:
                # found a new key/value pair
                key = mo.group( 1 ).strip().lower()
                val = line_buf[ mo.end(0) : ].strip()
                self.sections[ curr_section_name ][ key ] = val

    def get_string( self, section, key, default="" ):
        """Return a string config value."""
        val, text_type = self.__get_val( section, key, default )
        assert text_type is None
        return val

    def get_textval( self, section, key, default=None ):
        """Return a string config value.

        Awasu uses TextVal's to store feed content (e.g. feed titles, or item descriptions),
        where it is important to know whether the content is plain-text or HTML.
        """
        if default is None:
            default = ( "", ConfigFile.TVT_UNKNOWN )
        else:
            assert len(default) == 2
            assert isinstance( default[0], str )
            assert isinstance( default[1], int )
        val, text_type = self.__get_val( section, key, default[0] )
        if text_type is None:
            text_type = default[1]
        assert text_type is not None
        return ( val, text_type )

    def get_string_list( self, section, default=None ):
        """Return a list of string values."""
        vals = []
        for i in range( 1, sys.maxsize ):
            val, text_type = self.__get_val( section, str(i), "" )
            assert text_type is None
            if not val:
                break
            vals.append( val )
        if vals:
            return vals
        else:
            return default if default is not None else []

    def get_string_indirect( self, section, key, default="", required=False ):
        """Return a string config value, possibly from a file.

        NOTE: Awasu doesn't use this feature, but it's useful when writing extensions.
        """
        val, text_type = self.__get_val( section, key, default )
        assert text_type is None
        if os.path.isfile( val ):
            # a file was specified - return the string from that
            with open( val, "r", encoding="utf-8" ) as fp:
                val = fp.read()
        else:
            if required:
                raise RuntimeError( "Can't find file: "+val )
        return val

    def get_int( self, section, key, default=0 ):
        """Return an integer config value."""
        val, _ = self.__get_val( section, key, default )
        return int( val )

    def get_bool( self, section, key, default=False ):
        """Return a boolean config value."""
        val, _ = self.__get_val( section, key, default )
        if val.lower() in [ "1", "true", "yes", "on", "enable", "enabled" ]:
            return True
        if val.lower() in [ "0", "false", "no", "off", "disable", "disabled" ]:
            return False
        raise ValueError( "Invalid boolean: " + val )

    def __get_val( self, section, key, default ):
        """Return a raw config value.

        NOTE: A value that is present, but empty, is treated the same as
        a value that is not present i.e. it will return the default value.
        """
        val = self.sections.get( section.lower(), {} ).get( key.lower() )
        if not val:
            # NOTE: We can't pass the default value into get(), since we need to handle both
            # the case where the key is not present, and where the key is present but empty.
            val = "" if default is None else str(default)
        # decode any %XX characters
        val = re.sub( "%[0-9A-Fa-f]{2}",
            lambda mo: chr( int( mo.group()[1:], 16 ) ),
            val
        )
        # check for an Awasu TextVal type flag
        mo = re.search( r"\n\*(\d)$", val )
        if mo:
            return ( val[:mo.start(0)], int(mo.group(1)) )
        else:
            return ( val, None )

    def dump( self, out=sys.stdout ):
        """Dump the ConfigFile."""
        for section, keyvals in self.sections.items():
            print( "[{}]".format( section ), file=out )
            for key, val in keyvals.items():
                print( "{} = {}".format( key, val ), file=out )
            print( file=out )

# ---------------------------------------------------------------------

class ConfigFileTestCase( unittest.TestCase ):
    """Test this module."""

    def test_get_val( self ):
        """Test getting values from a ConfigFile."""

        # initialize
        config_file = ConfigFile( b"""
[section 1]
foo=bar
  theAnswer  =  42
empty =

  [  SECTION 2  ] ; a comment
    FOO  =  !!!
#comment=foo
 ; comment = bar

[utf-8]
japan=\xE6\x97\xA5\xE6\x9C\xAC

[TextVal]
UnknownContent = This is some unknown content.%0A*0
PlainTextContent = This is some plain-text content.%0A*1
HtmlContent = This is some HTML content.%0A*2
BadTextValType = This content has a bad TextVal type.%0A*9
Empty=%0A*0
""" )

        # do simple tests
        self.assertEqual( config_file.get_string( "section 1", "foo" ), "bar" )
        self.assertEqual( config_file.get_int( "section 1", "theanswer" ), 42 )
        self.assertEqual( config_file.get_string( "section 2", "foo" ), "!!!" )
        self.assertEqual( config_file.get_string( "section 2", "theanswer" ), "" )
        self.assertEqual( config_file.get_string( "section 99", "foo" ), "" )

        # check that non-ASCII is being handled correctly
        val = config_file.get_string( "utf-8", "japan" )
        self.assertEqual( len(val), 2 )
        self.assertEqual( ord(val[0]), 0x65E5 )
        self.assertEqual( ord(val[1]), 0x672C )

        # check TextVal's
        self.assertEqual(
            config_file.get_textval( "TextVal", "UnknownContent" ),
            ( "This is some unknown content.", ConfigFile.TVT_UNKNOWN )
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "PlainTextContent" ),
            ( "This is some plain-text content.", ConfigFile.TVT_PLAINTEXT )
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "HtmlContent" ),
            ( "This is some HTML content.", ConfigFile.TVT_HTML )
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "BadTextValType" ),
            ( "This content has a bad TextVal type.", 9 )
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "Empty" ),
            ( "", ConfigFile.TVT_UNKNOWN )
        )

        # check handling of default values
        self.assertEqual(
            config_file.get_string( "section 1", "empty" ),
            ""
        )
        self.assertEqual(
            config_file.get_string( "section 1", "empty", "<default>" ),
            "<default>"
        )
        self.assertEqual(
            config_file.get_string( "section 1", "_not_present_", "<default>" ),
            "<default>"
        )
        self.assertEqual(
            config_file.get_string( "section 1", "_not_present_" ),
            ""
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "Empty" ),
            ( "", ConfigFile.TVT_UNKNOWN )
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "Empty", ("<default>",ConfigFile.TVT_HTML) ),
            ( "", ConfigFile.TVT_UNKNOWN ) # nb: because this key/value is present, but empty
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "_not_present_" ),
            ( "", ConfigFile.TVT_UNKNOWN )
        )
        self.assertEqual(
            config_file.get_textval( "TextVal", "_not_present_", ("<default>",ConfigFile.TVT_HTML) ),
            ( "<default>", ConfigFile.TVT_HTML )
        )

    def test_unicode( self ):
        """Test handling of Unicode content."""

        # initialize
        config_file = ConfigFile( b"""
[section-\xE6\x97\xA5\xE6\x9C\xAC]
japan = \xE6\x97\xA5\xE6\x9C\xAC
\xE6\x97\xA5\xE6\x9C\xAC = nihon
""" )

        # check that non-ASCII is being handled correctly
        def check( key, expected_val ):
            val = config_file.get_string( "section-\u65e5\u672c", key )
            self.assertIs( type(val), str )
            self.assertEqual( val, expected_val )
        check( "japan", "\u65e5\u672c" )
        check( "\u65e5\u672c", "nihon" )

# ---------------------------------------------------------------------

if __name__ == "__main__":
    if len( sys.argv ) == 1:
        # run the unit tests
        unittest.main()
    else:
        # load and dump the specified config file
        _config_file = ConfigFile( sys.argv[1] )
        _config_file.dump()
