from setuptools import setup

setup(
      name = "fake_addon"
    , version = "0.1"
    , packages = ['fake_addon']

    , entry_points =
      { "option_merge.addons":
        [ "fake1 = fake_addon"
        , "same = fake_addon.same"
        , "badresult = fake_addon.badresult"
        ]
      }
    )

