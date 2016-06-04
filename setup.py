from setuptools import setup, find_packages
from option_merge import VERSION

setup(
      name = "option_merge"
    , version = VERSION
    , packages = ['option_merge'] + ['option_merge.%s' % pkg for pkg in find_packages('option_merge')]
    , include_package_data = True

    , install_requires =
      [ 'six'
      ]

    , extras_require =
      { "tests":
        [ "noseOfYeti>=1.4.9"
        , "nose"
        , "mock"
        , 'delfick_error==1.7.3'
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
