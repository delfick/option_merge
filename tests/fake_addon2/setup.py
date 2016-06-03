from setuptools import setup

setup(
      name = "fake_addon2"
    , version = "0.1"
    , packages = ['fake_addon2']

    , entry_points =
      { "option_merge.addons":
        [ "fake2 = fake_addon2"
        , "unimportable = fake_addon2.unimportable"
        , "same = fake_addon2.same"
        , "nohook = fake_addon2.no_hook"
        ]
      }
    )

