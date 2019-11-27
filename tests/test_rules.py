#!/usr/bin/env python3
"""
Created on Mon Nov 18 11:43:12 2019

@author: mikhail-matrosov
"""

import pytest

from pycoercer import Validator, pycoercer_schema


def coerce_gender(value, args=None):
    return {
        'male': 'male',
        '1': 'male',
        'true': 'male',
        'female': 'female',
        '0': 'female',
        'false': 'female'
    }[str(value).lower()]


def test_nullable():
    v = Validator({
        'x': {'nullable': True, 'type': 'str'},
        'y': {'nullable': True, 'type': 'str', 'if_null': -1},
        'z': {'nullable': True, 'type': 'str', 'if_null': '{MY_PARAM}'}
    })

    assert v['x']('Hey!') == ('Hey!', None)
    assert v['x']({}) == (None, 'Input type must be str')
    assert v['x'](None) == (None, None)
    assert v['y']('Hey!') == ('Hey!', None)
    assert v['y'](None) == (-1, None)
    assert v['z']('Hey!') == ('Hey!', None)
    assert v['z'](None, {'MY_PARAM': -2}) == (-2, None)


def test_number():
    v = Validator({
        'n': {'type': 'number'},
        'f': {'type': 'float'},
        'i': {'type': 'int'}
    })

    assert v['n'](1) == (1, None)
    assert v['n'](1.2) == (1.2, None)
    assert v['n']('1') == (None, 'Input type must be number')

    assert v['f'](1) == (None, 'Input type must be float')
    assert v['f'](1.2) == (1.2, None)
    assert v['f']('1') == (None, 'Input type must be float')

    assert v['i'](1) == (1, None)
    assert v['i'](1.2) == (None, 'Input type must be int')
    assert v['i']('1') == (None, 'Input type must be int')


def test_coerce():
    v = Validator({
        'n': {'coerce': 'number'},
        's': {'coerce': 'str'},
        'b': {'coerce': 'bool'},
        'g': {'coerce': 'gender'}
    })

    v.coerce_gender = coerce_gender

    assert v['n'](1) == (1, None)
    assert v['n'](1.2) == (1.2, None)
    assert v['n']('1') == (1, None)
    assert v['n']('1.2') == (1.2, None)
    assert v['n']('que?') == (None, 'Input is not coercible to number')

    assert v['s'](1) == ('1', None)
    assert v['s'](1.2) == ('1.2', None)
    assert v['s']('1') == ('1', None)
    assert v['s']({}) == ('{}', None)
    assert v['s'](None) == ('None', None)

    assert v['b'](True) == (True, None)
    assert v['b'](1) == (True, None)
    assert v['b']('Yes') == (True, None)
    assert v['b']('1.0') == (True, None)
    assert v['b'](0) == (False, None)
    assert v['b'](False) == (False, None)
    assert v['b']('N') == (False, None)
    assert v['b']({}) == (None, 'Input is not coercible to bool')
    assert v['b'](5) == (None, 'Input is not coercible to bool')
    assert v['b']('qwe') == (None, 'Input is not coercible to bool')

    assert v['g']('female') == ('female', None)
    assert v['g'](1) == ('male', None)
    assert v['g'](False) == ('female', None)
    assert v['g'](2) == (None, 'Input is not coercible to gender')
    assert v['g']({}) == (None, 'Input is not coercible to gender')
    assert v['g'](None) == (None, 'Input is not coercible to gender')


def test_overwrite_default_coercion():
    v = Validator()
    v.coerce_bool = lambda val, args: {'foo': True, 'bar': False}[val]
    v['b'] = {'coerce': 'bool'}

    assert v['b']('foo') == (True, None)
    assert v['b']('bar') == (False, None)
    assert v['b']('baz') == (None, 'Input is not coercible to bool')


def test_regex():
    v = Validator({
        'a': {'regex': '.*'},
        'b': {'regex': 'b+'},
        'c': {'regex': r'c\\+'},
        'q1': {'regex': '"+'},
        'q2': {'regex': "'+"}
    })

    assert v['a']('qwe') == ('qwe', None)

    assert v['b']('bbbb') == ('bbbb', None)
    assert v['b']('') == (None, 'Input must match regex: b+')
    assert v['b']('abc') == (None, 'Input must match regex: b+')

    assert v['c']('c\\') == ('c\\', None)
    assert v['c']('c') == (None, r'Input must match regex: c\\+')

    assert v['q1']('"""') == ('"""', None)
    assert v['q1']("''") == (None, 'Input must match regex: "+')
    assert v['q2']("'''") == ("'''", None)
    assert v['q2']('""') == (None, "Input must match regex: '+")


def test_map():
    v = Validator({
        'x': {'map': {'a': 1, 'b': 2}}
    })

    assert v['x'](3) == (3, None)
    assert v['x']('a') == (1, None)
    assert v['x']('b') == (2, None)
    assert v['x']('c') == ('c', None)
    assert v['x']({}) == ({}, None)


def test_enum():
    v = Validator({
        'x': {'enum': [1, '2']},
        'y': {'enum': [1.0, '2', {}, None]}
    })

    assert v['x'](1) == (1, None)
    assert v['x']('1') == (None, "Input must be one of [1, '2']")
    assert v['x'](2) == (None, "Input must be one of [1, '2']")
    assert v['x']('2') == ('2', None)
    assert v['x']({}) == (None, "Input must be one of [1, '2']")
    assert v['x'](None) == (None, "Input must be one of [1, '2']")

    assert v['y'](1) == (1, None)
    assert v['y'](1.0) == (1, None)
    assert v['y']('1') == (None, "Input must be one of [1.0, '2', {}, None]")
    assert v['y'](2) == (None, "Input must be one of [1.0, '2', {}, None]")
    assert v['y']('2') == ('2', None)
    assert v['y']({}) == ({}, None)
    assert v['y'](None) == (None, None)


def test_minmax():
    v = Validator({
        'n': {'min': -10, 'max': 15},
        'w': {'min': 'flight', 'max': 'somewhere'},
    })

    assert v['n'](-11) == (None, 'Input must be at least -10')
    assert v['n'](-10) == (-10, None)
    assert v['n'](1) == (1, None)
    assert v['n'](15) == (15, None)
    assert v['n'](16) == (None, 'Input must be at most 15')

    assert v['w']('chicken') == (None, 'Input must be at least "flight"')
    assert v['w']('flight') == ('flight', None)
    assert v['w']('potato') == ('potato', None)
    assert v['w']('somewhere') == ('somewhere', None)
    assert v['w']('space') == (None, 'Input must be at most "somewhere"')


def test_minmax_len():
    v = Validator({
        'x': {'min_len': 2, 'max_len': 3}
    })

    assert v['x']([]) == (None, 'Input length must be at least 2')
    assert v['x']([1]) == (None, 'Input length must be at least 2')
    assert v['x']([1, 2]) == ([1, 2], None)
    assert v['x']([1, 2, 3]) == ([1, 2, 3], None)
    assert v['x']([1, 2, 3, 4]) == (None, 'Input length must be at most 3')

    assert v['x']('') == (None, 'Input length must be at least 2')
    assert v['x']('a') == (None, 'Input length must be at least 2')
    assert v['x']('ab') == ('ab', None)
    assert v['x']('abc') == ('abc', None)
    assert v['x']('abcd') == (None, 'Input length must be at most 3')

    assert v['x']({}) == (None, 'Input length must be at least 2')
    assert v['x']({1: 1}) == (None, 'Input length must be at least 2')
    assert v['x']({1: 1, 2: 2}) == ({1: 1, 2: 2}, None)
    assert v['x']({1: 1, 2: 2, 3: 3}) == ({1: 1, 2: 2, 3: 3}, None)
    assert v['x']({1: 1, 2: 2, 3: 3, 4: 4}) == (None, 'Input length must be at most 3')

    assert v['x'](set()) == (None, 'Input length must be at least 2')
    assert v['x']({1}) == (None, 'Input length must be at least 2')
    assert v['x']({1, 2}) == ({1, 2}, None)
    assert v['x']({1, 2, 3}) == ({1, 2, 3}, None)
    assert v['x']({1, 2, 3, 4}) == (None, 'Input length must be at most 3')


def test_one_any_of():
    v = Validator({
        'a1': {'any_of': [{'type': 'int'}, {'type': 'str'}]},
        'a2': {'any_of': [{'type': 'float'}, {'type': 'number'}]},
        'ac': {'any_of': [{'coerce': 'int'}, {'coerce': 'str'}]},
        'o1': {'one_of': [{'type': 'int'}, {'type': 'str'}]},
        'o2': {'one_of': [{'type': 'float'}, {'type': 'number'}]},
        'oc': {'one_of': [{'coerce': 'int'}, {'coerce': 'str'}]}
    })

    assert v['a1'](1) == (1, None)
    assert v['a1'](1.5) == (None, 'Input must satisfy any of 2 rules:\n'
                                  '1: ^ type must be int\n'
                                  '2: ^ type must be str')
    assert v['a1']('q') == ('q', None)
    assert v['a2'](1) == (1, None)
    assert v['a2'](1.5) == (1.5, None)
    assert v['a2']('q') == (None, 'Input must satisfy any of 2 rules:\n'
                                  '1: ^ type must be float\n'
                                  '2: ^ type must be number')
    assert v['ac'](1) == (1, None)
    assert v['ac']('1') == (1, None)
    assert v['ac']('1.5e2') == (150, None)
    assert v['ac']({}) == ('{}', None)

    assert v['o1'](1) == (1, None)
    assert v['o1'](1.5) == (None, 'Input must satisfy exactly one of 2 rules:\n'
                                  '1: ^ type must be int\n'
                                  '2: ^ type must be str')
    assert v['o1']('q') == ('q', None)
    assert v['o2'](1) == (1, None)
    assert v['o2'](1.5) == (None, 'Input must satisfy exactly one of 2 rules:\n'
                                  '1: ok\n'
                                  '2: ok')
    assert v['o2']('q') == (None, 'Input must satisfy exactly one of 2 rules:\n'
                                  '1: ^ type must be float\n'
                                  '2: ^ type must be number')
    assert v['oc'](1) == (None, 'Input must satisfy exactly one of 2 rules:\n'
                                '1: ok\n'
                                '2: ok')
    assert v['oc']('1') == (None, 'Input must satisfy exactly one of 2 rules:\n'
                                  '1: ok\n'
                                  '2: ok')
    assert v['oc']({}) == ('{}', None)


def test_default():
    v = Validator({
        'a': {
            'type': 'dict',
            'items': {
                'd': {'default': 5}
            }
        }
    })

    assert v['a']({'d': 3}) == ({'d': 3}, None)
    assert v['a']({}) == ({'d': 5}, None)


def test_default_args():
    v = Validator({
        'a': {
            'type': 'dict',
            'items': {
                'd': {'default': '{MY_PARAM}'}
            }
        }
    })

    assert v['a']({'d': 3}) == ({'d': 3}, None)
    assert v['a']({}, {'MY_PARAM': 5}) == ({'d': 5}, None)


def test_required():
    schema = {
        'a': {
            'type': 'dict',
            'items': {'x': {}}
        },
        'b': {
            'type': 'dict',
            'items': {'x': {'required': True}}
        },
        'c': {
            'type': 'dict',
            'items': {'x': {}},
            'require_all': True
        },
        'd': {
            'type': 'dict',
            'items': {'x': {'required': False}},
            'require_all': True
        },
        'e': {
            'type': 'dict',
            'items': {'x': {}},
            'require_all': False
        },
        'f': {
            'type': 'dict',
            'items': {'x': {'required': True}},
            'require_all': False
        }
    }
    vn = Validator(schema, require_all=0)
    vr = Validator(schema, require_all=1)

    for schema in 'abcdef':
        assert vn[schema]({'x': 3}) == ({'x': 3}, None)
        assert vr[schema]({'x': 3}) == ({'x': 3}, None)

    assert vn['a']({}) == ({}, None)
    assert vn['b']({}) == (None, 'Input.x is required')
    assert vn['c']({}) == (None, 'Input.x is required')
    assert vn['d']({}) == ({}, None)
    assert vn['e']({}) == ({}, None)
    assert vn['f']({}) == (None, 'Input.x is required')

    assert vr['a']({}) == (None, 'Input.x is required')
    assert vr['b']({}) == (None, 'Input.x is required')
    assert vr['c']({}) == (None, 'Input.x is required')
    assert vr['d']({}) == ({}, None)
    assert vr['e']({}) == ({}, None)
    assert vr['f']({}) == (None, 'Input.x is required')


def test_rename():
    v = Validator({
        'x': {
            'type': 'dict',
            'items': {
                'a': {'type': 'int', 'rename': 'b'},
                'b': {'type': 'str'}
            },
            'require_all': False
        }
    })

    assert v['x']({'a': 1}) == ({'b': 1}, None)
    assert v['x']({'a': '1'}) == (None, 'Input.a type must be int')
    assert v['x']({'b': '1'}) == ({'b': '1'}, None)
    assert v['x']({'b': 1}) == (None, 'Input.b type must be str')


def test_synonyms():
    v = Validator({
        'x': {
            'type': 'dict',
            'items': {
                'a': {'type': 'int', 'synonyms': ['b', 'c']},
            }
        }
    })

    assert v['x']({'a': 1}) == ({'a': 1}, None)
    assert v['x']({'c': 1}) == ({'a': 1}, None)
    assert v['x']({'a': '1'}) == (None, 'Input.a type must be int')
    assert v['x']({'b': '1'}) == (None, 'Input.b type must be int')


def test_allow_unknown():
    schema = {
        'a': {
            'type': 'dict',
            'items': {'x': {}}
        },
        'b': {
            'type': 'dict',
            'items': {'x': {}},
            'allow_unknown': True
        },
        'c': {
            'type': 'dict',
            'items': {'x': {}},
            'allow_unknown': False
        }
    }
    vn = Validator(schema, allow_unknown=0)
    va = Validator(schema, allow_unknown=1)

    for schema in 'abc':
        assert vn[schema]({'x': 3}) == ({'x': 3}, None)
        assert va[schema]({'x': 3}) == ({'x': 3}, None)

    assert vn['a']({'u': 5}) == (None, "Input must not contain keys {'u'}")
    assert vn['b']({'u': 5}) == ({'u': 5}, None)
    assert vn['c']({'u': 5}) == (None, "Input must not contain keys {'u'}")

    assert va['a']({'u': 5}) == ({'u': 5}, None)
    assert va['b']({'u': 5}) == ({'u': 5}, None)
    assert va['c']({'u': 5}) == (None, "Input must not contain keys {'u'}")


def test_purge_unknown():
    schema = {
        'a': {
            'type': 'dict',
            'items': {'x': {}}
        },
        'b': {
            'type': 'dict',
            'items': {'x': {}},
            'purge_unknown': True
        },
        'c': {
            'type': 'dict',
            'items': {'x': {}},
            'purge_unknown': False
        }
        # TODO: lists
    }
    vn = Validator(schema, allow_unknown=1, purge_unknown=0)
    vp = Validator(schema, allow_unknown=1, purge_unknown=1)

    for schema in 'abc':
        assert vn[schema]({'x': 3}) == ({'x': 3}, None)
        assert vp[schema]({'x': 3}) == ({'x': 3}, None)

    d = {'x': 3, 'u': 5}
    assert vn['a'](d) == (d, None)
    assert vn['b'](d) == ({'x': 3}, None)
    assert vn['c'](d) == (d, None)

    assert vp['a'](d) == ({'x': 3}, None)
    assert vp['b'](d) == ({'x': 3}, None)
    assert vp['c'](d) == (d, None)


def test_values():
    v = Validator({
        'd': {
            'type': 'dict',
            'values': {'type': 'int'}
        },
        'l': {
            'type': 'list',
            'values': {'type': 'int'}
        }
    })

    assert v['d']({}) == ({}, None)
    assert v['d']({'x': 1, 'y': 2}) == ({'x': 1, 'y': 2}, None)
    assert v['d']({'x': 1, 'y': 's'}) == (None, 'Input.y type must be int')

    assert v['l']([]) == ([], None)
    assert v['l']([1, 2]) == ([1, 2], None)
    assert v['l']([1, 's']) == (None, 'Input[1] type must be int')


def test_post_coerce():
    v = Validator({
        'a': {
            'coerce': 'int',
            'post_coerce': 'str'
        },
        'g': {
            'coerce': 'int',
            'post_coerce': 'gender'
        }
    })

    v.coerce_gender = coerce_gender

    assert v['a'](1) == ('1', None)
    assert v['a'](1.2) == ('1', None)
    assert v['a']('1') == ('1', None)
    assert v['a']({}) == (None, 'Input is not coercible to int')

    assert v['g'](1) == ('male', None)
    assert v['g'](1.2) == ('male', None)
    assert v['g']('1') == ('male', None)
    assert v['g'](2) == (None, 'Input is not coercible to gender')
    assert v['g']('2') == (None, 'Input is not coercible to gender')
    assert v['g']({}) == (None, 'Input is not coercible to int')


def test_schema_examples():
    v = Validator({
        'a': {
            'enum': [1, 2, 3],
            'examples': [2, 3],
            'negative_examples': [0, 4]
        },
        'b': {
            'type': 'dict',
            'items': {
                'x': {
                    'enum': [1, 2],
                    'examples': [1]
                }
            },
            'examples': [{'x': 2}]
        }
    })

    bad_schemas = [
        {
            'enum': [1, 2, 3],
            'examples': [1, 5]
        },
        {
            'enum': [1, 2, 3],
            'negative_examples': [1]
        },
        {
            'type': 'dict',
            'items': {
                'x': {
                    'enum': [1, 2],
                    'examples': [5]
                }
            },
            'examples': [{'x': 2}]
        },
        {
            'type': 'dict',
            'items': {
                'x': {
                    'enum': [1, 2],
                    'examples': [1]
                }
            },
            'examples': [{'x': 5}]
        }
    ]

    for schema in bad_schemas:
        try:
            v['x'] = schema
            assert 0, 'Must throw exception'
        except ValueError:
            pass


def test_self_validate():
    v = Validator(pycoercer_schema)
    assert v['obj_dict'](pycoercer_schema) == (pycoercer_schema, None)


#def test_options_baking():
#    v = Validator({
#        'a': {
#            'type': 'dict',
#            'items': {'x': {'type': 'int'}}
#        },
#        'b': {
#            'type': 'dict',
#            'items': {'x': {'type': 'int'}},
#            'require_all': True
#        }
#    })
