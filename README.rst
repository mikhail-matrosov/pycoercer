Pycoercer
=========

Fast Python JSON schema validation and normalization

.. code-block:: python

  v = Validator({
    'User': {
      'items': {
        'name': {'coerce': 'str'},
        'gender': {
          'map': {
            'woman': 'female',
            'man': 'male',
            None: 'other'  # Map everything else
          },
          'synonyms': ['sex']
        },
        'country': {
          'default': '{GEOIP2_COUNTRY}'
        }
      }
    }
  })

  args = {'GEOIP2_COUNTRY': 'UK'}

  v['User']({
    'name': 123,
    'sex': 'woman'
  }, args)

  # Returns:
  # 
  # ({
  #    'name': '123',
  #    'gender': 'female',
  #    'country': 'UK'
  #  },
  #  None)  # Error description


Features
--------

Pycoercer was created to meet the actual production needs for web apps
development - inspired by `jsonschema`_ and `Cerberus`_,
it also implements additional features:
- Can validate, normalize (or coerce) dicts and lists
- Fast - the schema is compiled into python code
- Clean `rules system`_ with a predictable order of execution
- Parametric `default` and `if_null` values
- Keywords for data coercion: `synonyms`, `map`, and `post_coerce`
- Check `examples` against the schema definition


Installation
------------

.. code-block:: console

  $ pip install pycoercer


Documentation
-------------

Complete documentation will be [sometime][docs]


Testing
-------

.. code-block:: console

  $ pytest


.. _jsonschema: https://json-schema.org/
.. _Cerberus: https://python-cerberus.org/
.. _rules system: docs/index.md