#!/usr/bin/env python3
"""
Created on Fri Sep 20 12:37:07 2019

@author: mikhail-matrosov
"""

from pycoercer.basic_validator import BasicValidator


class Options():
    def __init__(self,
                 allow_unkown=True,
                 purge_unkown=False,
                 require_all=False,
                 break_loops=True,
                 load_as_jsonschema=False,
                 validate_schemas=True,
                 **_):
        self.allow_unkown = allow_unkown
        self.purge_unkown = purge_unkown
        self.require_all = require_all
        self.break_loops = break_loops  # Makes Phimera ~10-15% slower
        self.load_as_jsonschema = load_as_jsonschema
        self.validate_schemas = validate_schemas

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def replace(self, **kwargs):
        '''Returns a new instance'''
        data = self.__dict__.copy()
        data.update(kwargs)
        return Options(**data)


class Validator(BasicValidator):
    def __init__(self, schemas: dict = None, options=None, **kwargs):
        super().__init__()
        self.registry = {}
        self.options = (options or Options()).replace(**kwargs)

        if schemas:
            self.update(schemas)

    def __getitem__(self, k):
        return self.registry[k]

    def __setitem__(self, key, schema: dict):
        self.update({key: schema})

    def update(self, schemas: dict, options=None, **kwargs):
        options = (options or self.options).replace(**kwargs)
        self.options, options_backup = options, self.options

        if options.load_as_jsonschema:
            schemas = {k: {'type': 'dict', 'schema': v}
                       for k, v in schemas.items()}

        # Validate input schemas
        if options.validate_schemas:
            schemas, err = pycoercer_schema_validator(schemas)
            if err:
                raise ValueError(err)

        self._schemas.update(schemas)

        # Code generation
        self.registry.update({
            name: self.generate_function(schema, options, name)
            for name, schema in schemas.items()
        })

        # Validate examples
        try:
            if options.validate_schemas:
                self._test_examples()
        finally:  # even if exception
            self._positive_examples.clear()
            self._negative_examples.clear()

        self.options = options_backup


pycoercer_schema = {
    'str': {'type': 'str'},
    'int': {'type': 'int'},
    'bool': {'type': 'bool'},

    'rules': {
        'type': 'dict',
        'items': {
            'title': None,
            'description': None,

            'examples': {'type': 'list'},
            'negative_examples': {'type': 'list'},

            'allow_unkown': 'bool',
            'purge_unkown': 'bool',

            'rename': 'str',
            'synonyms': {'type': 'list'},
            'required': 'bool',
            'require_all': 'bool',

            'nullable': 'bool',
            'if_null': {},
            'default': {},

            'type': {
                'nullable': True,
                'type': 'str',
                'map': {
                    'object': 'dict',
                    'array': 'list',
                    'string': 'str',
                    'integer': 'int',
                    'boolean': 'bool',
                    'None': None,
                    'null': None
                },
                'enum': ['dict', 'list', 'str', 'int', 'float', 'number',
                         'bool']
            },
            'coerce': 'str',
            'map': {
                'type': 'dict',
                'allow_unkown': True
            },
            'enum': {
                'type': 'list',
                'synonyms': ['allowed']
            },
            'regex': {
                'type': 'str',
                'synonyms': ['pattern']
            },
            'items': {
                'type': 'dict',  # TODO: list notation for lists
                'values': 'obj',
                'synonyms': ['schema', 'properties']
            },
            'rules': {'type': 'str'},
            'keys': {
                'rules': 'obj',
                'synonyms': ['keysrules']
            },
            'values': {
                'rules': 'obj',
                'synonyms': ['valuesrules']
            },
            'min': {},
            'max': {},
            'min_len': {
                'type': 'int',
                'synonyms': ['minLength', 'minlength']
            },
            'max_len': {
                'type': 'int',
                'synonyms': ['maxLength', 'maxlength']
            },
            'one_of': {
                'type': 'list',
                'values': 'obj',
                'synonyms': ['oneOf', 'oneof']
            },
            'any_of': {
                'type': 'list',
                'values': 'obj',
                'synonyms': ['anyOf', 'anyof']
            },
            'post_coerce': 'str'

            # todo: if_invalid
        }
    },

    'obj': {
        'any_of': [
            {'type': None},
            'str',
            'rules'
        ]
    },

    'obj_dict': {
        'type': 'dict',
        'values': 'obj'
    }
}

_pcsv = Validator(
    pycoercer_schema,
    allow_unkown=False,
    purge_unkown=False,
    require_all=False,
    break_loops=True,
    load_as_jsonschema=False,
    validate_schemas=False)

pycoercer_schema_validator = _pcsv['obj_dict']
