from collections import namedtuple, Mapping, Sequence
from copy import deepcopy

DictDiff = namedtuple("DictDiff", "added removed modified")
COLLECTION = (Sequence, set)  # tuple, list, set


class NotFound:
    def __repr__(self):
        return "<NotFound>"


class DictCompare:
    NOT_FOUND = NotFound()

    @classmethod
    def _filter_dict_keys(cls, d, **kwargs):
        ignore_keys = kwargs.get('ignore_keys', [])
        return set(k for k in d if not k.startswith('_') and k not in ignore_keys)

    @classmethod
    def delete_key_chain_from_dict(cls, orig_dict, mapped_keys, keys):
        d = orig_dict
        for k in mapped_keys[:-1]:
            d = d.get(k, {})
        if not d:
            return
        for _keys in (mapped_keys, keys):
            try:
                d.pop(_keys[-1])
                return
            except KeyError:
                # try the other key
                pass

    @classmethod
    def update_dict(cls, orig_dict, new_dict):
        for key, val in new_dict.items():
            if isinstance(val, Mapping):
                orig_dict[key] = cls.update_dict(orig_dict.get(key, {}) or {}, val)
            else:
                orig_dict[key] = new_dict[key]
        return orig_dict

    @classmethod
    def _fix_key(cls, key, value, fix_funcs=None, **kwargs):
        fix_funcs = fix_funcs or {}
        for func in fix_funcs.get(key, []):
            try:
                value = func(value)
            except:
                break
        return value

    @classmethod
    def _get_shared(cls, benchmark, test, **kwargs):
        ignore_keys = kwargs.get('ignore_keys', [])
        shared = []
        for bench_key, mapped_keys in cls.iterator(benchmark.keys(), **kwargs):
            if bench_key.startswith("_") or bench_key in ignore_keys:
                continue
            mapped_value = cls.get_nested_value(mapped_keys, test, cls.NOT_FOUND)
            if mapped_value is not cls.NOT_FOUND:
                shared.append((bench_key, mapped_keys, mapped_value))
        return shared

    @classmethod
    def _modify(cls, benchmark, test, avoid_inner_order, **kwargs):
        modified = {}

        shared = cls._get_shared(benchmark, test, **kwargs)

        for bench_key, mapped_keys, test_value in shared:
            bench_value = benchmark.get(bench_key)

            bench_value = cls._fix_key(bench_key, bench_value, **kwargs)
            test_value = cls._fix_key(mapped_keys[0], test_value, **kwargs)

            if avoid_inner_order and all(isinstance(v, COLLECTION) for v in (bench_value, test_value)):
                compare_bench_value = list(set(bench_value))
                compare_test_value = list(set(test_value))
            else:
                compare_bench_value = bench_value
                compare_test_value = test_value

            if compare_bench_value != compare_test_value:
                if all(isinstance(v, Mapping) for v in (bench_value, test_value)):
                    kwargs.pop("column_mapping", {})
                    _diff = cls.compare(bench_value, test_value, avoid_inner_order=avoid_inner_order, **kwargs)
                    diff = _diff.modified
                    diff.update({(rmv,): (cls.NOT_FOUND, value) for rmv, value in _diff.removed.items()})
                    diff.update({(add,): (value, cls.NOT_FOUND) for add, value in _diff.added.items()})
                    bench_key = (bench_key,) if isinstance(bench_key, str) else bench_key
                    for k, v in diff.items():
                        modified[bench_key + k] = v
                else:
                    # old, new
                    diff = (bench_value, test_value)
                    modified[(bench_key,)] = diff
        return modified

    @classmethod
    def compare(cls, benchmark, test, avoid_inner_order=True, **kwargs):
        column_mapping = kwargs.get('column_mapping', {})

        bench_keys = cls._filter_dict_keys(benchmark, **kwargs)
        bench_mapped_keys = set(o[0] if isinstance(o, tuple) else o
                                for o in set(column_mapping.get(o, o) for o in bench_keys))
        bench_mapped_keys = cls._filter_dict_keys(bench_mapped_keys, **kwargs)
        test_keys = cls._filter_dict_keys(test, **kwargs)

        added = {add: benchmark[add] for add in bench_mapped_keys - test_keys}
        removed = {rmv: test[rmv] for rmv in test_keys - bench_mapped_keys}
        modified = cls._modify(benchmark, test, avoid_inner_order=avoid_inner_order, **kwargs)
        return DictDiff(added, removed, modified)

    @classmethod
    def get_nested_value(cls, keys, _dict, default):
        _test = deepcopy(_dict)
        try:
            for k in keys:
                _test = _test[k]
            return _test
        except KeyError:
            if isinstance(default, Exception):
                raise default
            return default

    @classmethod
    def iterator(cls, collection, **kwargs):
        column_mapping = kwargs.get('column_mapping', {})
        is_dict_type = isinstance(collection, Mapping)
        for item in collection:
            item_tup = item if isinstance(item, tuple) else (item,)
            mapped_keys = tuple([column_mapping.get(x, x) for x in item_tup])
            if is_dict_type:
                yield (item, mapped_keys), collection[item]
            else:
                yield item, mapped_keys

    @classmethod
    def _get_dict_to_update(cls, diffs, benchmark, test, **kwargs):
        delta = {}
        changes = []
        # added
        for (keys, mapped_keys), _ in cls.iterator(diffs.added, **kwargs):
            entry = {keys: benchmark[keys]}
            changes.append(f"[+] {entry}")
            cls.update_dict(delta, entry)

        modification_fields = set(kwargs.get('modification_fields', []))
        changed_fields = kwargs.get('changed_fields', [])
        # modified
        for (keys, mapped_keys), (old_val, new_val) in cls.iterator(diffs.modified, **kwargs):
            if old_val is cls.NOT_FOUND:
                cls.delete_key_chain_from_dict(test, mapped_keys, keys)
                continue

            must_modify = all(k not in modification_fields for k in mapped_keys)
            if new_val is cls.NOT_FOUND or must_modify:
                value = old_val
                _from = new_val
            else:
                # if 'keys' are changed_fields then we keep the change and choose new_val, else take original value
                value = new_val if list(keys) in changed_fields else old_val
                _from = new_val if value == old_val else old_val

            nested_dict_to_update = cls.convert_to_nested_dicts(mapped_keys, value=value)

            changes.append("[!] '{}={}' ==> '{}'".format('->'.join([s if isinstance(s, str) else
                                                                    '=>'.join(list(s)) for s in mapped_keys]),
                                                         _from, value))
            cls.update_dict(delta, nested_dict_to_update)
        return delta, changes

    @classmethod
    def update(cls, benchmark, test, avoid_inner_order=True, **kwargs):
        # Compare and update
        diffs = cls.compare(benchmark, test, avoid_inner_order=avoid_inner_order, **kwargs)
        delta, changes = cls._get_dict_to_update(diffs=diffs, benchmark=benchmark, test=test, **kwargs)
        cls.update_dict(test, delta)
        return changes

    @staticmethod
    def convert_to_nested_dicts(keys, value=None):
        # return nested dicts from tuple of strings: (1,2,3) ==> {1:{2:{3:value}}}
        if isinstance(keys, str):
            return keys
        t = value
        for k in reversed(keys):
            if not isinstance(k, str):
                k = k[-1]
            d = {k: t}
            t = d
        return t
