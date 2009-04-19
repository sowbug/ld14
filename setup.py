# Thanks to
#http://www.moviepartners.com/blog/2009/03/20/making-py2exe-play-nice-with-pygame/

# py2exe setup program
from distutils.core import setup
import py2exe, pygame
import sys
import os
import glob, shutil
sys.argv.append('py2exe')

VERSION = '38.07' # Number of hours/minutes into compo
AUTHOR_NAME = 'Mike Tsao (Sowbug)'
AUTHOR_EMAIL = 'mike.tsao@gmail.com'
AUTHOR_URL = 'http://www.sowbug.org/'
PRODUCT_NAME = 'Ludum Dare 14 Entry'
SCRIPT_MAIN = 'src/ld14.py'
VERSIONSTRING = PRODUCT_NAME + ' ALPHA ' + VERSION
ICONFILE = 'assets/icon.ico'

INCLUDE_STUFF = [
                 'encodings',
                 'encodings.latin_1',
                 ]

MODULE_EXCLUDES = [
'email',
'AppKit',
'Foundation',
'bdb',
'difflib',
'tcl',
'Tkinter',
'Tkconstants',
'curses',
'distutils',
'setuptools',
'urllib',
'urllib2',
'urlparse',
'BaseHTTPServer',
'_LWPCookieJar',
'_MozillaCookieJar',
'ftplib',
'gopherlib',
'_ssl',
'htmllib',
'httplib',
'mimetools',
'mimetypes',
'rfc822',
'tty',
'webbrowser',
'socket',
'hashlib',
'base64',
'compiler',
'pydoc'
]

# Remove the build tree on exit automatically
REMOVE_BUILD_ON_EXIT = True

if os.path.exists('dist/'): shutil.rmtree('dist/')
 
extra_files = [
('', ['README.txt', 'ld14_log.txt']),
('assets', glob.glob(os.path.join('assets', '*.png'))),
('assets', glob.glob(os.path.join('assets', '*.wav'))),
('assets', glob.glob(os.path.join('assets', '*.ico'))),
('assets', glob.glob(os.path.join('assets', '*.sfs'))),
('fonts', glob.glob(os.path.join('fonts', '*.otf'))),
('src', glob.glob(os.path.join('src', '*.py'))),
]

setup(windows=[{'script': SCRIPT_MAIN,
'other_resources': [(u'VERSIONTAG', 1, VERSIONSTRING)],
'icon_resources': [(1, ICONFILE)]
}],
options={'py2exe': { 'optimize': 2,
                     'includes': INCLUDE_STUFF,
                     'compressed': 1,
                     'ascii': 1,
                     'bundle_files': 2,
                     'ignores': ['tcl', 'AppKit', 'Numeric', 'Foundation'],
                     'excludes': MODULE_EXCLUDES} },
name=PRODUCT_NAME,
version=VERSION,
data_files=extra_files,
zipfile=None,
author=AUTHOR_NAME,
author_email=AUTHOR_EMAIL,
url=AUTHOR_URL
)
 
# Remove the build tree
if REMOVE_BUILD_ON_EXIT: shutil.rmtree('build/')
