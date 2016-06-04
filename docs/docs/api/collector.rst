.. _collector:

Collector
=========

.. automodule:: option_merge.collector

Hooks
-----

.. autoclass:: option_merge.collector.Collector
    :members: BadFileErrorKls, BadConfigurationErrorKls
              , alter_clone_args_dict, find_missing_config, extra_prepare, extra_prepare_after_activation, home_dir_configuration_location
              , read_file, start_configuration, add_configuration, extra_configuration_collection, setup

Usage
-----

.. automethod:: option_merge.collector.Collector.prepare

.. automethod:: option_merge.collector.Collector.clone

.. automethod:: option_merge.collector.Collector.register_addons

.. automethod:: option_merge.collector.Collector.register_converters
