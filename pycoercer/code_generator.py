#!/usr/bin/env python3
"""
Created on Wed Nov 20 18:55:05 2019

@author: mikhail-matrosov
"""

import re
from pickle import dumps as pdumps


def hash_obj(*args):
    return '_{:x}'.format(abs(hash(pdumps(args))))


def escape(s):
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


def as_code(o):
    return f'"{escape(o)}"' if isinstance(o, str) else str(o)


def indent(seq, ind=1):
    return ('    '*ind + s for s in seq)


def store_in_locals(obj, _locals, attr_name=None):
    name = hash_obj(obj)
    _locals[name] = getattr(obj, attr_name) if attr_name else obj
    return name


def cg_type(val):
    if val is None:
        return [f'if o is not None:',
                f'    return None, " type must be NoneType"']
    return [('if not (isinstance(o, float) or isinstance(o, int)):'
             if val == 'number' else
            f'if not isinstance(o, {val}):'),
            f'    return None, " type must be {val}"']


def cg_enum(val, _locals):
    name = store_in_locals(val.copy(), _locals)
    try:
        sname = store_in_locals(set(val), _locals)
        return [
             'try:',
            f'    if o not in {sname}:',
            f'        return None, f" must be one of {{{name}}}"',
             'except TypeError:',  # If o is not Hashable
            f'    return None, f" must be one of {{{name}}}"']
    except TypeError:  # Not hashable
        return [f'if o not in {name}:',
                f'    return None, f" must be one of {{{name}}}"']


def cg_min(val):
    return [f'if o < {as_code(val)}:',
            f"    return None, ' must be at least {as_code(val)}'"]


def cg_max(val):
    return [f'if o > {as_code(val)}:',
            f"    return None, ' must be at most {as_code(val)}'"]


def cg_min_len(val):
    return [f'if len(o) < {val}:',
            f'    return None, " length must be at least {val}"']


def cg_max_len(val):
    return [f'if len(o) > {val}:',
            f'    return None, " length must be at most {val}"']


def cg_regex(val, _locals):
    name = store_in_locals(re.compile(val), _locals, 'fullmatch')
    return [f'if not {name}(o):',
            f'    return None, " must match regex: {{}}".format({name}.__self__.pattern)']


def cg_coerce_int():
    return ['try: o = int(o)',
            'except:',
            '    try: o = int(float(o))',
            '    except:',
            '        return None, " is not coercible to int"']


def cg_coerce_float():
    return ['try: o = float(o)',
            'except:',
            '    return None, " is not coercible to float"']


def cg_coerce_number():
    return ['if not isinstance(o, float):',
            '    try: o = int(o)',
            '    except:',
            '        try: o = float(o)',
            '        except:',
            '            return None, " is not coercible to number"']


def cg_coerce_str():
    yield 'o = str(o)'


def cg_map(val, _locals):
    name = store_in_locals(val.copy(), _locals, 'get')
    default = f'{name}(None)' if None in val else 'o'
    return [f'try: o = {name}(o, {default})',
             'except TypeError: pass']  # In case not Hashable


def cg_any_of(names):
    for i, name in enumerate(names):
        yield 4*i*' ' + f'r{i}, err{i} = {name}(o, args)'
        yield 4*i*' ' + f'if err{i}:'

    N = len(names)
    errs = ', '.join(f'_indent_str(err{i})' for i in range(N))
    fmt = ''.join(f'\\n{i+1}: ^{{}}' for i in range(N))
    yield 4*N*' ' + f'return None, " must satisfy any of {N} rules:{fmt}".format({errs})'
    yield from (4*i*' ' + f'else: o = r{i}' for i in reversed(range(N)))


def cg_one_of(names):
    N = len(names)
    errs = '"^"+_indent_str(e) if e else "ok" for x, e in rs'
    fmt = ''.join(f'\\n{i+1}: {{}}' for i in range(N))
    calls = ', '.join(f'{name}(o, args)' for name in names)
    return [
    f'rs = [{calls}]',
     'valid = [x for x, e in rs if not e]',
     'if len(valid) == 1:',
     '    o = valid[0]',
     'else:',
    f'    fmt = ({errs})',
    f'    return None, " must satisfy exactly one of {N} rules:{fmt}".format(*fmt)']


def cg_coerce(name, input_code='o'):
    try:
        return globals()['cg_coerce_'+name]()
    except KeyError:
        return [
         'try:',
        f'    o = self.coerce_{name}({input_code}, args)',
         'except:',
        f'    if not hasattr(self, "coerce_{name}"):',
        f'        raise AttributeError("Validator has no attribute coerce_{name}")',
        f'    return None, " is not coercible to {name}"']


def cg_nullable(if_null, post_coerce):
    if isinstance(if_null, str) and re.match('{.+}', if_null):
        if_null = f'args[{as_code(if_null[1:-1])}]'
    else:
        if_null = as_code(if_null)
    yield 'if o is None:'
    if post_coerce:
        yield from cg_coerce(post_coerce, if_null)
    else:
        yield f'    return {if_null}, None'


def cg_rules(self, rules, options):
    _locals = self.__dict__
    rules = rules or {}
    rget = rules.get
    globs = globals()
    resolve = self.resolve_rules
    rhash, rules = resolve(rules, options)

    # Resolve rules from 'rules' rule
    v = rget('rules')
    if v:
        old_rules, rules = rules, resolve(v)[1].copy()
        rules.update(old_rules)
        rget = rules.get

    if rget('examples'):
        self._positive_examples[rhash] = (rules, rget('examples'))

    if rget('negative_examples'):
        self._negative_examples[rhash] = (rules, rget('negative_examples'))

    if rget('nullable') or rget("if_null"):
        yield from cg_nullable(rget("if_null"), rget('post_coerce'))

    if 'type' in rules:
        yield from cg_type(rules['type'])

    v = rget('coerce')
    if v:
        yield from cg_coerce(v)

    v = rget('regex')
    if v:
        yield from cg_regex(v, _locals)

    purge_unkown = rget('purge_unkown', options.purge_unkown)
    has_schema = any(map(rget, 'items values keys pattern_items'.split()))

    rtype = rget('type', rget('coerce'))
    if rtype in {'dict', 'list'} or has_schema:
        if rtype == 'dict' and purge_unkown:
            yield 'o, orig = {}, o'
        else:
            yield 'o, orig = o.copy(), o'

    inner_options = self.options.replace(**rules)

    if has_schema:
        if rtype == 'list':
            yield from cg_list_items(self, **rules, options=inner_options)
        else:
            yield from cg_dict_items(self, **rules, options=inner_options)

    v = rget('map')
    if v:
        yield from cg_map(v, _locals)

    v = rget('enum')
    if v:
        yield from cg_enum(v, _locals)

    for r in ['min', 'max', 'min_len', 'max_len']:
        v = rget(r)
        if v is not None:
            yield from globs['cg_' + r](v)

    for k in ['any_of', 'one_of']:
        v = rget(k)
        if v:
            names = [resolve(r, inner_options)[0] for r in v]
            yield from globs['cg_' + k](names)

    v = rget('post_coerce')
    if v:
        yield from cg_coerce(v)


def cg_default(k, k_to, rules, require_all):
    if 'default' in rules:
        v = rules['default']
        if isinstance(v, str) and re.fullmatch('{.+}', v):
            default = f'args[{as_code(v[1:-1])}]'
        else:
            default = as_code(v)

        yield  'else:'
        yield f'    o[{k_to}] = {default}'
    elif rules.get('required', require_all):
        yield  'else:'
        yield f'    return None, ".{escape(k)} is required"'


def cg_key_value(k, fname, rules, require_all):
    k_from = as_code(k)
    k_to = as_code(rules['rename']) if rules and 'rename' in rules else k_from
    val_source = (f'o.pop({k_from}, orig[{k_from}])'
                  if 'rename' in rules else f'orig[{k_from}]')
    yield from [
        f'if {k_from} in orig:',
        f'    o[{k_to}], err = {fname}({val_source}, args)',
         '    if err:',
        f'        return None, ".{escape(k)}" + err']

    yield from cg_default(k, k_to, rules, require_all)


def cg_dict_item(self, key, rules, require_all, store_known_keys):
    fname, rules = self.resolve_rules(rules)
    k_from = as_code(key)
    k_to = as_code(rules['rename']) if rules and 'rename' in rules else k_from

    if rules is NotImplemented:
        yield from cg_key_value(key, fname, {}, require_all)
    elif rules:
        synonyms = rules.get('synonyms')
        if synonyms:
            store_known_keys.update(synonyms)
#            val_source = ('o.pop(k, orig[k])'
#                          if 'rename' in rules else 'orig[k]')
            val_source = 'o.pop(k, orig[k])'
            yield from [
                f'for k in {[key] + synonyms}:',
                 '    if k in orig:',
                f'        o[{k_to}], err = {fname}({val_source}, args)',
                 '        if err:',
                 '            return None, f".{k}{err}"',
                 '        break']
            yield from cg_default(key, k_to, rules, require_all)
        else:
            yield from cg_key_value(key, fname, rules, require_all)
    else:
        yield f'if {k_from} in orig:'
        yield f'    o[{k_to}] = orig[{k_from}]'
        yield from cg_default(key, k_to, {}, require_all)


def cg_rule_key_value(self, keys, values, err_key_fmt='.{}'):
    if keys is None:
        k_to, ind = 'k', ''
    else:
        k_fname, k_rules = self.resolve_rules(keys)
        if k_rules == {}:
            k_to, ind = 'k', ''
        else:
            yield f'tk, k_err = {k_fname}(k, args)'
            yield  'if not k_err:'
            k_to, ind = 'tk', '    '

    if values:
        v_fname, v_rules = self.resolve_rules(values)
        if v_rules == {}:
            yield ind + f'o[{k_to}] = orig[k]'
        else:
            yield from [
            ind + f'o[{k_to}], err = {v_fname}(orig[k], args)',
            ind +  'if err:',
            ind + f'    return None, "{err_key_fmt}{{}}".format(k, err)',
            ind +  'continue']
    else:
        yield ind + f'o[{k_to}] = orig[k]'


def cg_pattern_item(self, pattern_items):
    _locals = self.__dict__
    resolve = self.resolve_rules

    yield 'if isinstance(k, str):'

    for ptrn in sorted(pattern_items, key=lambda p: (-len(p), p)):
        fname, rules = resolve(pattern_items[ptrn])

        # TODO: check if rules is NotImplemented
        name = store_in_locals(re.compile(ptrn), _locals, 'fullmatch')
        tk = as_code(rules['rename']) if rules and 'rename' in rules else 'k'

        yield from [
            f'    if {name}(k):',
            f'        o[{tk}], err = {fname}(orig[k], args)',
             '        if err:',
             '            return None, f".{k}{err}"',
             '        continue']
        # TODO: required and default


def cg_dict_items(self, items=None, pattern_items=None, keys=None, values=None,
                  options=None, **_):
    known_keys = set(items) if items else set()
    _locals = self.__dict__

    if items:
        for key, rules in items.items():
            yield from cg_dict_item(self, key, rules, options.require_all, known_keys)

    pattern_items = pattern_items or {}
    if pattern_items or keys is not None or values is not None:
        if known_keys:
            kk_name = store_in_locals(known_keys, _locals)
            yield f'for k in set(orig) - {kk_name}:'
        else:
            yield 'for k in orig:'

        if pattern_items:
            yield from indent(cg_pattern_item(self, pattern_items))

        if keys is not None or values is not None:
            yield from indent(cg_rule_key_value(self, keys, values))

        if not options.allow_unkown:
            yield '    return None, f" must not contain key {k}"'

    elif not options.allow_unkown:
        kk_name = store_in_locals(known_keys, _locals)
        yield from [
        f'forbidden_keys = set(orig) - {kk_name}',
         'if forbidden_keys:',
         '    return None, f" must not contain keys {forbidden_keys}"']


def cg_list_items(self, keys=None, values=None, **_):
    yield 'for k in range(len(orig)):'

    if values is not None:
        yield from indent(cg_rule_key_value(
                self, keys, values, err_key_fmt='[{}]'))

