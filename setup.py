from setuptools import setup, find_packages

setup(
      name = "option_merge"
    , version = "0.9.9.8"
    , packages = ['option_merge'] + ['option_merge.%s' % pkg for pkg in find_packages('option_merge')]
    , include_package_data = True

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
