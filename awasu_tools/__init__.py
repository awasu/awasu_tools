""" Tools for writing Awasu extensions."""

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
import shutil
import re
import time
import datetime
import calendar
import pprint
import xml.dom.minidom
import xml.parsers.expat

# ---------------------------------------------------------------------

def safe_xml( val ) :
    """Convert a value into something that's safe to insert into XML."""
    if val is None : return ""
    if type(val) is unicode :
        val = val.encode( "utf-8" )
    elif type(val) is not str :
        val = str( val )
    val = val.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    val = val.replace( "\"" , "&quot;" ) # nb: in case the value is an attribute
    return val

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def pretty_xml( val ) :
    """Prettify XML."""
    assert type(val) is str # nb: in case someone accidentally passes in unicode
    try :
        # NOTE: We remove blank lines generated by toprettyxml() (because it preserves
        # whitespace between XML tags).
        buf = xml.dom.minidom.parseString( val ).toprettyxml( indent="  " )
        lines = buf.split( "\n" )
        if lines[0] == "<?xml version=\"1.0\" ?>" :
            del lines[0]
        return "\n".join( [ x for x in lines if x.strip() ] )
    except xml.parsers.expat.ExpatError :
        # NOTE: If the XML is invalid, we just return it verbatim.
        return "*** WARNING: Invalid XML ***\n" + val

# ---------------------------------------------------------------------

def parse_rfc2822_timestamp( tstamp ) :
    """Parse an RFC 2822 timestamp."""

    # we sometimes get timestamps without the DOW :shrug:
    if re.match( "[A-Za-z]{3}, " , tstamp ) :
        tstamp = tstamp[5:]

    # parse the date
    mo = re.match( "[0-9][0-9]?" , tstamp ) # nb: we sometimes get single-digit dates :-/
    if not mo :
        return None # nb: we sometimes get weird rubbish :-/
    date = int( mo.group() )
    tstamp = tstamp[mo.end()+1:]

    # parse the rest of the timestamp
    #   0----5----0----5----0----5
    #   Apr 2014 15:07:51 +0000
    # NOTE: We can't use strptime(), since it will look for month names
    # using the current locale, but we need English.
    month_names = { "jan": 1 , "feb": 2 , "mar": 3 , "apr": 4 , "may": 5 , "jun": 6 , "jul": 7 , "aug": 8 , "sep": 9 , "oct": 10 , "nov": 11 , "dec": 12 }
    month = month_names[ tstamp[:3].lower() ]
    year = int( tstamp[4:8] )
    hours = int( tstamp[9:11] )
    minutes = int( tstamp[12:14] )
    seconds = int( tstamp[15:17] )
    tstamp2 = datetime.datetime( year , month , date , hours , minutes , seconds )
    # adjust for the time zone
    if tstamp[18] in ("+","-") :
        tz_delta = 60 * int(tstamp[19:21]) + int(tstamp[21:23])
        tz_delta *= -1 if tstamp[18] == "+" else +1
        tstamp2 += datetime.timedelta( seconds=60*tz_delta )
    return calendar.timegm( tstamp2.utctimetuple() )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def make_iso8601_timestamp( tstamp ) :
    """Return an ISO 8601 timestamp (for Atom feeds)."""
    if type(tstamp) in (int,long) :
        tstamp = time.gmtime( tstamp )
    return "{year:4d}-{month:02d}-{date:02d}T{hours:02d}:{minutes:02d}:{seconds:02d}Z".format(
        year = tstamp.tm_year ,
        month = tstamp.tm_mon ,
        date = tstamp.tm_mday ,
        hours = tstamp.tm_hour ,
        minutes = tstamp.tm_min ,
        seconds = tstamp.tm_sec
    )

# ---------------------------------------------------------------------

def make_atom_text_type( mime_type ) :
    """Convert a MIME type to an Atom text type."""
    if mime_type == "text/plain" :
        return "text"
    elif mime_type == "text/html" :
        return "html"
    return "???"

# ---------------------------------------------------------------------

def change_extn( fname , extn ) :
    """Change the extension of a filename."""
    dname , fname = os.path.split( fname )
    fname = ("{}{}" if extn.startswith(".") else "{}.{}").format( os.path.splitext(fname)[0] , extn )
    return os.path.join( dname , fname )

def make_dir( dname ) :
    """Create a directory."""
    if os.path.isdir( dname ) :
        return
    try :
        os.makedirs( dname )
    except :
        logging.log_msg( "WARNING: Can't create directory: {}".format( dname ) ) # nb: we try to keep going

def remove_file( fname ) :
    """Remove a file (if it exists)."""
    if os.path.isfile( fname ) :
        os.unlink( fname )

def remove_dir( dname ) :
    """Remove a directory (if it exists)."""
    if os.path.isdir( dname ) :
        shutil.rmtree( dname )

# ---------------------------------------------------------------------

def dump_bytes( buf , caption="" , prefix="" , fp=sys.stdout ) :
    """Formatted byte dump."""
    if caption :
        print >>fp , caption # nb: no line prefix
    # dump the value as bytes
    for line_no in range((len(buf)+15)/16) :
        print >>fp , "{}{:04x}:".format( prefix , 16*line_no ) ,
        row_bytes = buf[ 16*line_no : 16*line_no+16 ]
        line_buf = " ".join( [ "{:02x}".format(ord(ch)) for ch in row_bytes ] )
        if len(line_buf) > 23 : # nb: 23 = 8 hex values (2 digits each), plus 7 separators
            line_buf = "{} {}".format( line_buf[:23] , line_buf[23:] )
        line_buf += " "*(48-len(line_buf))
        print >>fp , line_buf ,
        print >>fp , "|" , "".join( [ ch if 32 <= ord(ch) < 127 else "." for ch in row_bytes ] )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def safe_string( val ) :
    """Safe string representation."""
    if type(val) is str :
        return pprint.pformat(val)[1:-1] # nb: remove quotes :-/
    elif type(val) is unicode :
        return pprint.pformat(val)[2:-1] # nb: remove quotes :-/
    else :
        return str(val)
