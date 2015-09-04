from setuptools import setup, find_packages, Extension
from Cython.Distutils import build_ext

path = Extension("option_merge.path", ["option_merge/path.pyx"])
merge = Extension("option_merge.merge", ["option_merge/merge.pyx"])
helper = Extension("option_merge.helper", ["option_merge/helper.pyx"])
storage = Extension("option_merge.storage", ["option_merge/storage.pyx"])
value_at = Extension("option_merge.value_at", ["option_merge/value_at.pyx"])
converter = Extension("option_merge.converter", ["option_merge/converter.pyx"])
versioning = Extension("option_merge.versioning", ["option_merge/versioning.pyx"])

setup(
      name = "option_merge"
    , version = "0.9.9.1"
    , packages = ['option_merge'] + ['option_merge.%s' % pkg for pkg in find_packages('option_merge')]
    , include_package_data = True

    , cmdclass = {"build_ext": build_ext}
    , ext_modules = [versioning, path, value_at, storage, helper, merge, converter]

    , install_requires =
      [ 'six'
      , 'delfick_error>=1.6'
      ]

    , extras_require =
      { "tests":
        [ "noseOfYeti>=1.4.9"
        , "nose"
        , "mock"
        ]
      }

    # metadata for upload to PyPI
    , url = "http://github.com/delfick/option_merge"
    , author = "Stephen Moore"
    , author_email = "stephen@delfick.com"
    , description = "Code to deeply merge multiple python dictionaries"
    , license = "WTFPL"
    , keywords = "deep merge"
    )
