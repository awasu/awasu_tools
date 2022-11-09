""" Classes for generating feeds. """

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
import time

from awasu_tools.utils import safe_xml, pretty_xml
from awasu_tools.log import log_msg, log_raw_msg

# ---------------------------------------------------------------------

class Feed:
    """Container for a feed and its items."""

    def __init__( self, title, home_url, description=None, image_url=None, updated_time=None, extra_args=None ):
        """Initialize the Feed."""
        self.title = title
        self.home_url = home_url
        self.description = description
        self.image_url = image_url
        self.updated_time = updated_time if updated_time else time.time()
        self.extra_args = extra_args
        self.feed_items = []

    def get_xml( self, templ=None, log=None ):
        """Generate the feed XML."""
        # initialize
        if templ:
            assert isinstance( templ, str )
        else:
            # use the default template
            templ = """<?xml version="1.0" encoding="UTF-8"?>""" "\n" \
                    """<feed xmlns="http://www.w3.org/2005/Atom" xmlns:xh="http://www.w3.org/1999/xhtml">""" "\n" \
                    """<title type="text">{title}</title>""" "\n" \
                    """<subtitle type="html">{description}</subtitle>""" "\n" \
                    """<link href="{url}" />""" "\n" \
                    """<logo>{image_url}</logo>""" "\n" \
                    """<updated>{updated_time}</updated>""" "\n" \
                    """{feed_items}""" "\n" \
                    """</feed>"""
        # generate the feed XML
        args = {
            "title": self.title,
            "description": self.description,
            "url": self.home_url,
            "image_url": self.image_url,
            "updated_time": _format_time( self.updated_time ),
        }
        if self.image_url and not self.image_url.startswith( ( "http://", "https://", "file://" ) ):
            # NOTE: We assume image_url has been set to point to a file in our directory.
            ### IMPORTANT CAVEAT ###
            # If the channel image is accessed as a local file, it won't show properly
            # because of CORS (although it seems to work if the channel is opened in Awasu) :-/
            # Things will also definitely not work if the channel summary page is loaded
            # from another computer, via a remote Awasu API call, since the other computer
            # obviously won't have access to file on the local computer. We can live with this
            # for now; if it's really a problem for someone, they can copy the logo file
            # somewhere accessible, and override the image URL in the feed template.
            # FUDGE! The directory name could contain non-ASCII characters!
            dname = os.path.split( sys.argv[0] )[0].decode( "windows-1252" )
            args["image_url"] = "file:///" + os.path.join( dname, self.image_url )
        if self.extra_args:
            args.update( self.extra_args )
        args = {
            k: safe_xml( v ) if v is not None else ""
            for k, v in args.items()
        }
        args["feed_items"] = "\n".join(
            fi.get_xml(log) for fi in self.feed_items
        )
        if not self.feed_items:
            # tidy up the output if there are no feed items
            pos = templ.find( "{feed_items}\n" )
            if pos >= 0:
                templ = templ[:pos] + templ[pos+13:]
        return templ.format( **args )

# ---------------------------------------------------------------------

class FeedItem:
    """Container for a feed item."""

    def __init__( self, title, url, content=None, updated_time=None, templ=None, extra_args=None ):
        """Initialize the FeedItem."""
        self.title = title
        self.url = url
        self.content = content
        self.updated_time = updated_time
        self.templ = templ
        self.extra_args = extra_args

    def get_xml( self, log=None ):
        """Generate the feed item XML."""
        # initialize
        if self.templ:
            assert isinstance( self.templ, str )
            templ = self.templ
        else:
            # use the default template
            templ = """<entry>""" \
                    """<title type="text">{title}</title>""" \
                    """<link href="{url}" />""" \
                    """<updated>{updated_time}</updated>""" \
                    """<content type="html">{content}</content>""" \
                    """</entry>"""
        # prepare to generate the feed item XML
        args = {
            "title": self.title,
            "url": self.url,
            "updated_time": _format_time( self.updated_time ),
            "content": self.content,
        }
        if self.extra_args:
            args.update( self.extra_args )
        if log:
            log_msg( "" )
            log_msg( "Generating feed item..." )
            for key, val in args.items():
                log_msg( "- {} = {}", key, "" if val is None else val )
        # generate the feed item XML
        args = {
            k: safe_xml( v ) if v is not None else ""
            for k, v in args.items()
        }
        buf = templ.format( **args )
        if log:
            log_msg( "Generated feed item XML:" )
            log_raw_msg( pretty_xml( buf ) )
        return buf

# ---------------------------------------------------------------------

def _format_time( val ):
    """Format a time value for insertion into a feed."""
    if isinstance( val, float ):
        return time.strftime( "%Y-%m-%dT%H:%M:%SZ", time.gmtime( val ) )
    else:
        return val

# ---------------------------------------------------------------------

if __name__ == "__main__":
    # a simple example
    feed = Feed( "An example feed", "http://test.com" )
    feed.feed_items.append(
        FeedItem( "Feed item 1", "http://test.com/item1", "This is feed item #1" )
    )
    feed.feed_items.append(
        FeedItem( "Feed item 2", "http://test.com/item2", "This is feed item #2", time.time() )
    )
    print( feed.get_xml() )
