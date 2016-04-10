.. _converter:

Converter
=========

.. automodule:: option_merge.converter

Single Converter
----------------

.. autoclass:: option_merge.converter.Converter
    :members: __call__, matches

Group of converters
-------------------

.. autoclass:: option_merge.converter.Converters
    :members: __iter__, matches, converted, converted_val, waiting, done, started
