from setuptools import setup

APP = ['app01.py']
VERSION = '1.0.1'
OPTIONS = {
    'argv_emulation': False,
    'packages': ['flask', 'flask_cors', 'waitress'],
    'resources': ['app01_index.html'],
    'plist': {
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'LSMultipleInstancesProhibited': True,
    },
}

setup(
    app=APP,
    version=VERSION,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
