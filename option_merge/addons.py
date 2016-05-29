def find_input_algorithms(package="input_algorithms", version=">=0.5"):
    try:
        __import__(package)
    except ImportError:
        raise Exception("To use option_merge addons your program must also have {0} as a requirement".format(package))

    import pkg_resources
    try:
        pkg_resources.working_set.require(["{0}{1}".format(package, version)])
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict) as error:
        raise Exception("Have invalid version of {0}\terror={1}".format(package, error))

find_input_algorithms()
