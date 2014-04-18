from setuptools import setup

setup(
      name = "option_merge"
    , version = "0.1"
    , py_modules = ['option_merge']

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
