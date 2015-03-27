"""Loging services."""

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

import time

_log_file = None

# ---------------------------------------------------------------------

def log_msg( msg , *args , **kwargs ) :
    """Log a message."""
    if not _log_file : return
    if msg == "" :
        _log_file.write( "\n" )
        return
    # convert everything to UTF-8
    if type(msg) is unicode :
        msg = msg.encode( "utf-8" )
    args = [ x.encode("utf-8") if type(x) is unicode else x for x in args ]
    kwargs = { k: v.encode("utf-8") if type(v) is unicode else v for k,v in kwargs.items() }
    # log the message
    _log_file.write( "{} | ".format( time.strftime("%Y-%m-%d %H:%M:%S") ) )
    _log_file.write( msg.format( *args , **kwargs ) )
    _log_file.write( "\n" )
    _log_file.flush()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def log_raw_msg( msg ) :
    """Log a raw message."""
    if not _log_file : return
    if type(msg) is unicode :
        msg = msg.encode( "utf-8" )
    _log_file.write( msg )
    if not msg.endswith( "\n" ) :
        _log_file.write( "\n" )
    _log_file.flush()

# ---------------------------------------------------------------------

def init_logging( log_filename ) :
    """Initialize logging."""
    if not log_filename : return
    global _log_file
    try :
        if log_filename.startswith( "+" ) :
            # append to the log file
            _log_file = open( log_filename[1:] , "a" )
            _log_file.write( "\n\n\n=== NEW SESSION ===\n" )
        else :
            # start a new log file
            _log_file = open( log_filename , "w" )
    except IOError:
        pass
