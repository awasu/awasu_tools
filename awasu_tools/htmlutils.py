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

import bs4
import functools

# ---------------------------------------------------------------------

def strip_html( val , encoding , allow_non_html , sep=" " ) :
    soup = bs4.BeautifulSoup( val , from_encoding=encoding )
    elems = filter( 
        functools.partial( _is_visible_html_elem , allow_non_html ) ,
        soup.findAll( text=True )
    )
    elems = [ x.strip() for x in elems if x.strip() != "" ]
    return sep.join( elems )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def _is_visible_html_elem( allow_non_html , elem ) :
    if elem.parent.name in ["style","script","head","title"] :
        return False
    elif elem.parent.name == "[document]" and not allow_non_html :
        return False
    elif elem[:4].encode("utf-8") == "<!--" and elem[-3:].encode("utf-8") == "-->" :
        return False
    return True
