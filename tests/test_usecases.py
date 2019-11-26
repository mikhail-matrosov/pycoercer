#!/usr/bin/env python3
"""
Created on Mon Nov 18 11:43:12 2019

@author: mikhail-matrosov
"""

import pytest

from pycoercer import Validator, pycoercer_schema


def test_general():
    schemas = {
     'str': {'type': 'str'},
     'numbers': {'minlength': 2, 'type': 'list', 'values': {'type': 'int'}},

     'user': {
      'type': 'dict',
      'schema': {
        'id': {
         'type': 'int',
         'enum': [1, 2, 3, 4, 5],
         'min': 1,
         'max': 4},
       'name': {'type': 'str', 'regex': '\\S+'},
       'addr': {
        'type': 'dict',
        'schema': {
         'city': {'type': 'str'},
         'street': {'type': 'str'},
         'bld': {'type': 'str'}},
        'minlength': 2},
       'children': {
        'type': 'list',
        'values': {
          'type': 'dict',
          'schema': {'id': {'type': 'int'}}}},
       'favourite_numbers': 'numbers'
      }
     },

     'a': {'type': 'dict', 'schema': {'next': 'b'}},
     'b': {'type': 'dict', 'schema': {'next': 'a'}},

     'recursive': {'type': 'dict',
      'schema': {'id': {'type': 'int'}, 'v': 'recursive'}},
     'recursive_ptr': {'type': 'dict',
      'schema': {'id': {'type': 'int'}, 'v': {...}}},

     'universe_answer': {'coerce': 'int', 'default': 42},
     'universe_dict': {'type': 'dict',
      'schema': {'val': {'coerce': 'int', 'default': 123}}},
     'universe_dict_2': {'type': 'dict', 'schema': {'val': 'universe_answer'}},

     'rename': {'type': 'dict',
      'schema': {'val': {'coerce': 'int', 'default': 42, 'rename': 'qwe'}}},
     'anyof_validate': {'anyof': [{'type': 'int'},
       {'type': 'dict', 'allow_unkown': True},
       'str']},
     'oneof_validate': {'oneof': [{'type': 'int'},
       {'type': 'dict', 'allow_unkown': True},
       'str']},

     'valuesrules': {'type': 'dict',
      'valuesrules': {'type': 'str'},
      'allow_unkown': True},
     'valuesrules2': {
       'type': 'dict', 'valuesrules': 'str', 'allow_unkown': True}
    }

    schemas['recursive_ptr']['schema']['v'] = schemas['recursive_ptr']

    v = Validator(schemas)

    assert v['numbers']([1, 2, 3]) == ([1, 2, 3], None)
    assert v['numbers']([2, 'a']) == (None, 'Input[1] type must be int')
    assert v['numbers']([3]) == (None, 'Input length must be at least 2')

    assert v['user']({'id': 3,
                      'name': 'John',
                      'addr': {'city': '17'},
                      'children': [{'id': '5'}],
                      'favourite_numbers': [1]}) == (None, 'Input.addr length must be at least 2')
    assert v['user']({'id': 2,
                      'name': 'John',
                      'addr': {'city': 17, 'street': '5', 'bld': '6/2'},
                      'children': [{'id': '5'}],
                      'favourite_numbers': [1]}) == (None, 'Input.addr.city type must be str')

    d1 = d1['v'] = {'id': 1, 'v': {...}}
    d2 = d2['v'] = {'id': 's', 'v': {...}}
    assert v['recursive'](d1) == (d1, None)
    assert v['recursive'](d2) == (None, 'Input.id type must be int')
    assert v['recursive_ptr'](d1) == (d1, None)
    assert v['recursive_ptr'](d2) == (None, 'Input.id type must be int')

    assert v['universe_answer'](13) == (13, None)
    assert v['universe_answer'](13.1) == (13, None)
    assert v['universe_answer'](13.1) == (13, None)
    assert v['universe_dict']({'val': 13.1}) == ({'val': 13}, None)
    assert v['universe_dict']({}) == ({'val': 123}, None)
    assert v['universe_dict_2']({'val': 13.1}) == ({'val': 13}, None)
    assert v['universe_dict_2']({}) == ({'val': 42}, None)

    assert v['rename']({}) == ({'qwe': 42}, None)
    assert v['rename']({'val': 13.1}) == ({'qwe': 13}, None)

    assert v['anyof_validate'](42) == (42, None)
    assert v['anyof_validate']({'a': 1}) == ({'a': 1}, None)
    assert v['anyof_validate']('qwe') == ('qwe', None)
    assert v['anyof_validate'](None) == (None,
            'Input must satisfy any of 3 rules:\n'
            '1: ^ type must be int\n'
            '2: ^ type must be dict\n'
            '3: ^ type must be str')
    assert v['anyof_validate']([]) == (None,
            'Input must satisfy any of 3 rules:\n'
            '1: ^ type must be int\n'
            '2: ^ type must be dict\n'
            '3: ^ type must be str')

    assert v['oneof_validate'](42) == (42, None)
    assert v['oneof_validate']({'a': 1}) == ({'a': 1}, None)
    assert v['oneof_validate']('qwe') == ('qwe', None)
    assert v['oneof_validate'](None) == (None,
            'Input must satisfy exactly one of 3 rules:\n'
            '1: ^ type must be int\n'
            '2: ^ type must be dict\n'
            '3: ^ type must be str')
    assert v['oneof_validate']([]) == (None,
            'Input must satisfy exactly one of 3 rules:\n'
            '1: ^ type must be int\n'
            '2: ^ type must be dict\n'
            '3: ^ type must be str')

    assert v['valuesrules']({'a': 'b'}) == ({'a': 'b'}, None)
    assert v['valuesrules']({'a': 1}) == (None, 'Input.a type must be str')
    assert v['valuesrules2']({'a': 'b'}) == ({'a': 'b'}, None)
    assert v['valuesrules2']({'a': 1}) == (None, 'Input.a type must be str')
