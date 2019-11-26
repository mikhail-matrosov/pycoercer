#!/usr/bin/env python3
"""
Created on Wed Nov 20 19:35:46 2019

@author: mikhail-matrosov
"""

from functools import wraps
from pycoercer.code_generator import hash_obj, indent, cg_rules


def log(*a, **kw):
    # print(*a, **kw)
    pass


def loopbreaker(f):
    locks = set()

    @wraps(f)
    def wrapper(doc, args):
        k = id(doc)
        if k in locks:
            return doc, None

        locks.add(k)
        try:
            return f(doc, args)
        finally:  # Do after return
            locks.remove(k)

    wrapper.locks = locks
    return wrapper


def indent_str(s):
    return '\n  '.join(s.splitlines()) if '\n' in s else s


def schema_not_found(name):
    def f(o, args):
        raise NameError(f"Schema {name} was not defined")
    f.__name__ = name
    f.n_lines = 0
    return f


def _compile(statements, name, _locals, schema, break_loops=False):
    f_cache = _locals.setdefault('_f_cache', {})

    h = hash_obj(statements)
    if h in f_cache:
        f = _locals[name] = f_cache[h]
        log(f'# {name} = {f.__name__}\n')
        return f

    src = '\n'.join((f'def {name}(o, args):',
                     *indent(statements),
                     '    return o, None'))

    log(src + '\n')
    exec(src, _locals)

    func = _locals[name]
    if break_loops:
        func = loopbreaker(func)

    func.src = src
    func.schema = schema

    f_cache[h] = _locals[name] = func
    return func


def registry_wrapper(f):
    @wraps(f)
    def wrapper(obj, args=None):
        doc, err = f(obj, args)
        if err:
            return doc, 'Input' + err
        return doc, None

    return wrapper


class BasicValidator:
    def __init__(self):
        self._todo = []
        self._schemas = {}
        self._positive_examples = {}
        self._negative_examples = {}

        # Used by generated code
        self.self = self
        self._indent_str = indent_str

    def generate_function(self, rules, options, name):
        _locals = self.__dict__
        fname, rules = self.resolve_rules(rules, options)

        log(f'# {name}\n# {rules}')
        statements = list(cg_rules(self, rules, options))
        func = _compile(statements, fname, _locals, rules, break_loops=True)

        _locals[hash_obj(name)] = func  # Link previously loaded refs to f

        compiled_set = set()

        for task, opts in self._todo:
            fname = hash_obj(task, opts.__dict__)
            if fname not in compiled_set:  # Avoid recursion
                compiled_set.add(fname)
                log(f'# {task}')
                statements = list(cg_rules(self, task, opts))
                _compile(statements, fname, _locals, task)

        self._todo.clear()

        return registry_wrapper(func)

    def _test_examples(self):
        _locals = self.__dict__
        for fname, (rules, examples) in self._positive_examples.items():
            func = _locals[fname]
            for example in examples:
                if func(example, None)[1]:
                    raise ValueError('Failed validating example '
                                     f'{example} agains schema {rules}')

        for fname, (rules, examples) in self._negative_examples.items():
            func = _locals[fname]
            for example in examples:
                if not func(example, None)[1]:
                    raise ValueError('Failed validating negative example '
                                     f'{example} agains schema {rules}')

    def resolve_rules(self, rules, options=None):
        '''
        Idempotent
        return hash, {} - no schema to check
        return hash, NotImplemented - schema might come later
        '''

        if not options:
            options = self.options

        h = hash_obj(rules) if isinstance(rules, str) else hash_obj(rules, options.__dict__)

        if rules is NotImplemented:
            return h, NotImplemented

        if isinstance(rules, str):
            try:
                return h, (self._schemas[rules] or {})
            except KeyError:
                # Create a stub
                self.__dict__[h] = schema_not_found(rules)
                return h, NotImplemented
        elif rules:  # Avoid empty rulesets
            self._todo.append((rules, options))
            return h, rules
        return h, {}
