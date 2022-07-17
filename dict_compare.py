import logging
import pprint
from copy import deepcopy
from typing import Set, Any, Dict, Union, Mapping


COLLECTION_VAR = (tuple, list, set)

__all__ = (
    "compare",
    "update",
)
logger = logging.getLogger()


def update(benchmark, test, avoid_inner_order=True, **kwargs):
    """Compare first and then update according to the delta"""
    diffs = compare(benchmark, test, avoid_inner_order=avoid_inner_order, **kwargs)
    logger.info(f"[dict_compare] diffs = {diffs}")
    changes = get_dict_to_update(diffs=diffs, benchmark=benchmark, test=test, **kwargs)
    merge_dicts(test, changes)
    logger.info(f"[dict_compare] changes = {changes}")
    return changes


def compare(
    benchmark: dict,
    test: dict,
    key: str = None,
    avoid_inner_order: bool = False,
    **kwargs,
):
    """Compare between two dictionaries"""
    diffs = DictDiff.empty()

    # Top level
    diffs.update(added_keys(benchmark, test, **kwargs), key=key)
    diffs.update(removed_keys(benchmark, test, **kwargs), key=key)
    shared = get_shared_keys(benchmark, test, **kwargs)
    diffs.update(
        modified_keys(
            shared=shared, key=key, avoid_inner_order=avoid_inner_order, **kwargs
        )
    )
    return diffs


class DictDiff:
    def __init__(self, added=None, removed=None, modified=None):
        self.added = added or {}
        self.removed = removed or {}
        self.modified = modified or {}

    @classmethod
    def empty(cls):
        return cls({}, {}, {})

    @staticmethod
    def _update_dict(_from, _to, key):
        for k, v in _from.items():
            t = tuplize(key) if key else tuple()
            _to[t + tuplize(k)] = v

    def update(self, diff: "DictDiff", key: str = None):
        if not diff:
            return
        self._update_dict(diff.added, self.added, key=key)
        self._update_dict(diff.removed, self.removed, key=key)
        self._update_dict(diff.modified, self.modified, key=key)

    def __repr__(self):
        return pprint.pformat(self.changes, width=100, sort_dicts=False)

    @property
    def changes(self):
        return {"added": self.added, "removed": self.removed, "modified": self.modified}


class NotFoundSentinel:
    def __repr__(self):
        return "<NotFound>"


NOT_FOUND = NotFoundSentinel()


def added_keys(benchmark: Dict[str, Any], test: Dict[str, Any], **kwargs):
    bench_keys = get_valid_keys(benchmark, **kwargs)
    test_keys = bench_to_mapped_keys(bench_keys, **kwargs)
    added = {}
    for bench_key, mapped_key in zip(bench_keys, test_keys):
        if get_nested_value(mapped_key, test, NOT_FOUND) is NOT_FOUND:
            added[bench_key] = benchmark[bench_key]
    return DictDiff(added=added)


def removed_keys(benchmark: Dict[str, Any], test: Dict[str, Any], **kwargs):
    test_keys = get_valid_mapped_keys(test, **kwargs)
    bench_keys = mapped_to_bench_keys(test_keys, **kwargs)
    removed = {}
    for bench_key, mapped_key in zip(bench_keys, test_keys):
        if get_nested_value(bench_key, benchmark, NOT_FOUND) is NOT_FOUND:
            removed[mapped_key] = get_nested_value(
                mapped_key, test, IndexError(f"{mapped_key} is not found in test")
            )
    return DictDiff(removed=removed)


def modified_keys(shared, avoid_inner_order, key: str = None, **kwargs):
    modify_diff = DictDiff.empty()
    fix_funcs = kwargs.get("fix_funcs")

    for (bench_key, bench_value, mapped_keys, test_value) in shared:
        bench_value = fix_key(bench_key, bench_value, fix_funcs=fix_funcs)
        test_value = fix_key(mapped_keys, test_value, fix_funcs=fix_funcs)

        if avoid_inner_order and all(
            isinstance(v, COLLECTION_VAR) for v in (bench_value, test_value)
        ):
            compare_bench_value = value_of(bench_value)
            compare_test_value = value_of(test_value)
        else:
            compare_bench_value = bench_value
            compare_test_value = test_value

        if compare_bench_value != compare_test_value:
            if all(isinstance(v, Mapping) for v in (bench_value, test_value)):
                # recursively
                diffs = compare(
                    bench_value,
                    test_value,
                    key=bench_key,
                    avoid_inner_order=avoid_inner_order,
                    fix_funcs=fix_funcs,
                )
            else:
                diffs = DictDiff(modified={bench_key: (bench_value, test_value)})
            modify_diff.update(diffs, key=key)
    return modify_diff


def get_dict_to_update(diffs: DictDiff, benchmark: dict, test: dict, **kwargs):
    delta = {}

    for bench_key, mapped_keys in iterator(diffs.added, **kwargs):
        entry = convert_to_nested_dicts(
            mapped_keys,
            value=get_nested_value(
                bench_key, diffs.added, IndexError(f"{bench_key} is not found in added")
            ),
        )
        logger.info(f"[dict_compare] Add a new benchmark key: {entry}")
        merge_dicts(delta, entry)

    # fields that can be changed and take their changed value
    modification_fields = set(kwargs.get("modification_fields", []))

    # modified
    for bench_key, mapped_keys in iterator(diffs.modified, **kwargs):
        bench_value = get_nested_value(bench_key, benchmark, NOT_FOUND)
        mapped_value = get_nested_value(mapped_keys, test, NOT_FOUND)

        values = f"benchmark='{bench_value}', existing='{mapped_value}'"

        if bench_value is NOT_FOUND:
            exclude_dicts(test, mapped_keys, bench_key)
            continue

        must_modify = all(k not in modification_fields for k in mapped_keys)
        if mapped_value is NOT_FOUND or must_modify:
            # either the value is a new one or it was modified unofficially and should be restored
            value = bench_value
            modify_type = "modify key [benchmark]"
        else:
            # value was changed officially so we keep it and add the bench values
            type_bench = type(bench_value)
            type_mapped = type(mapped_value)
            if type_bench != type_mapped or type_bench not in COLLECTION_VAR:
                modify_type = "modify key [user-modified]"
                value = mapped_value
            else:
                modify_type = "modify key [benchmark & user-modified]"
                value = list(set(mapped_value).union(set(bench_value)))

        nested_dict_to_update = convert_to_nested_dicts(mapped_keys, value=value)
        logger.info(
            f"[dict_compare] {modify_type}: '{nested_dict_to_update}'. Values: [{values}]"
        )
        merge_dicts(delta, nested_dict_to_update)
    return delta


def bench_to_mapped_keys(bench_keys, **kwargs):
    column_mapping = kwargs.get("column_mapping", {})
    return tuple(column_mapping.get(o, o) for o in bench_keys)


def mapped_to_bench_keys(mapped_keys, **kwargs):
    column_mapping = kwargs.get("column_mapping", {})
    return tuple(
        (
            next((k for k, v in column_mapping.items() if v == mk), mk)
            for mk in mapped_keys
        )
    )


def get_valid_keys(d, **kwargs) -> Set[str]:
    return set(k for k in d if not key_to_ignore(k, **kwargs))


def get_valid_mapped_keys(test: Dict[str, Any], **kwargs):
    _dict = {k: test[k] for k in get_valid_keys(test, **kwargs)}
    return dict_to_key_chain(_dict)


def exclude_dicts(orig_dict, keys_chain, keys):
    d = orig_dict
    for k in keys_chain[:-1]:
        d = d.get(k, {})
    if not d:
        return
    for _keys in (keys_chain, keys):
        try:
            d.pop(_keys[-1])
            return
        except KeyError:
            # try the other key
            pass


def merge_dicts(orig_dict, new_dict):
    """Merge two dict by keeping both keys-values"""
    for key, val in new_dict.items():
        if isinstance(val, Mapping):
            orig_dict[key] = merge_dicts(orig_dict.get(key, {}) or {}, val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict


def fix_key(keys, value, fix_funcs):
    if not (fix_funcs := fix_funcs or {}):
        return value
    for key in tuplize(keys):
        for func in fix_funcs.get(key, []):
            try:
                value = func(value)
            except (Exception,):
                logger.error(
                    f"[dict_compare] Failed to fix key '{key}={value}' using '{func}'"
                )
                break
    return value


def get_shared_keys(benchmark, test, **kwargs):
    """Get shared keys between two dictionaries"""
    shared = []
    for bench_key, mapped_keys in iterator(benchmark, **kwargs):
        if key_to_ignore(bench_key, **kwargs):
            continue
        bench_value = benchmark.get(bench_key, NOT_FOUND)
        mapped_value = get_nested_value(mapped_keys, test, NOT_FOUND)
        if NOT_FOUND not in (mapped_value, bench_value):
            # take only keys in both dicts
            shared.append((bench_key, bench_value, mapped_keys, mapped_value))
    return shared


def key_to_ignore(key, **kwargs):
    return key.startswith("_") or key in kwargs.get("ignore_keys", [])


def value_of(item: Union[COLLECTION_VAR]):
    """align value of given collection to a sorted list"""
    try:
        return sorted(list(set(item)))
    except TypeError:
        return item


def get_nested_value(key, _dict, default):
    try:
        # try a direct dict-key
        return _dict[key]
    except KeyError:
        # try chained keys traverse
        _test = deepcopy(_dict)
        try:
            for k in key:
                _test = _test[k]
            return _test
        except KeyError as e:
            # default handling
            if isinstance(default, Exception):
                raise default from e
            return default


def iterator(collection, **kwargs):
    column_mapping = kwargs.get("column_mapping", {})
    for key in collection:
        mapped_keys = []
        for x in (column_mapping.get(x, x) for x in tuplize(key)):
            if isinstance(x, tuple):
                mapped_keys.extend(x)
            else:
                mapped_keys.append(x)
        yield key, tuple(mapped_keys)


def dict_to_key_chain(_dict: Dict[str, Any]):
    # convert a dict to tuple of key chain
    def _do_convert(inner_dict: Dict[str, Any]):
        # returns a tuple of key chain:
        # {1:{2:{3:v1, 4:v2}, 5:{6:v4}}, 7:v5} ==> [(1,2,3), (1,2,4), (1,5,6), (1,7)]
        key_chains = []
        for k, v in inner_dict.items():
            if isinstance(v, Dict):
                chain = _do_convert(v)
                for elem in chain:
                    elem = listify(elem)
                    elem.insert(0, k)
                    key_chains.append(elem)
            else:
                key_chains.append(k)
        return key_chains

    return [e if isinstance(e, str) else tuple(e) for e in _do_convert(_dict)]


def convert_to_nested_dicts(keys, value=None):
    # return nested dicts from tuple of strings: (1,2,3) ==> {1:{2:{3:value}}}
    if isinstance(keys, str):
        return keys
    t = value
    for k in reversed(keys):
        d = {k: t}
        t = d
    return t


def tuplize(item: Union[COLLECTION_VAR]):
    # convert to tuple
    return item if isinstance(item, tuple) else tuple(listify(item))


def listify(item: Union[COLLECTION_VAR]):
    # convert to list
    return item if isinstance(item, list) else [item]
