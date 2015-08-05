import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': 'atexit',
        'include_files': 'swift_fca/resources/images/swift_icon.svg'
    }
}

executables = [
    Executable('swift', base=base, icon='swift_fca/resources/images/swift_icon.ico'),
    Executable('swift-console')
]

setup(name='Swift FCA',
      version='0.1',
      description='FCA Converter',
      options=options,
      executables=executables
      )
