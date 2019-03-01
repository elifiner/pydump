try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'keepTrace',
    'url': 'https://github.com/internetimagery/keepTrace',
    'author': 'Jason Dixon',
    'author_email': 'jason.dixon.email@gmail.com',
    'version': '1.0.0',
    'py_modules': ['keepTrace'],
    'description': 'Pickle traceback support. Featuring debuggable restored tracebacks.'
}

setup(**config)
