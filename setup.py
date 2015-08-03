import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': 'atexit',
        'include_files': 'swift_icon.svg'
    }
}

executables = [
    Executable('gui_swift.py', base=base, icon='swift_icon.ico'),
    Executable('swift.py')
]

setup(name='FCA-Swift',
      version='0.1',
      description='FCA Convertor',
      options=options,
      executables=executables
      )
