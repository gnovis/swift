#!/usr/bin/python3

from swift_fca.swift_core.constants_fca import App
# Global variable to determine swift runing mode (gui/cli), do NOT use it for other stuff.
App.gui = True

from swift_fca.swift import main

if __name__ == '__main__':
    main()
