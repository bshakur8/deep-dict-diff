import logging
from copy import deepcopy
from typing import Set, Any, Dict, Union


COLLECTION_VAR = (tuple, list, set)

__all__ = (
    "compare",
    "update",
    "merge_dicts",
    "compare_with_reference",
)


def get_logger():
    base_logger = logging.getLogger()
    handler = logging.StreamHandler()
    log_format = "%(asctime)s [%(levelname)-1s]  %(message)s"
    handler.setFormatter(logging.Formatter(log_format))
    base_logger.addHandler(handler)
    base_logger.setLevel(logging.INFO)
    return base_logger


class DictCompareLogger:
    def __init__(self, diff_id=None, external_logger=None):
        diff_id = f"{diff_id}:" if diff_id else ""
        self._diff_id = diff_id or "[-]"
        if external_logger:
            self._logger_to_use = external_logger
        else:
            self._logger_to_use = get_logger()

    def __repr__(self):
        return f"[dict_compare_logger] {self._diff_id}"

    def _do_log(self, msg, level="info"):
        log_func = getattr(self._logger_to_use, level)
        log_func(f"[dict_compare] {self._diff_id} {msg}")

    def info(self, msg):
        return self._do_log(msg, "info")

    def warning(self, msg):
        return self._do_log(msg, "warning")

    def error(self, msg):
        return self._do_log(msg, "error")

    def summary(self, changes):
        if not changes:
            return
        diffs = []
        for key, change in changes.items():
            try:
                for change_key, change_value in change.items():
                    diffs.append(f"{key}.{change_key}='{change_value}'")
            except AttributeError:
                diffs.append(f"{key}='{change}'")
        pp_changes = "\n".join(diffs)
        self.info(f"Changes |->\n{pp_changes}")

    @classmethod
    def init_logger(cls, diff_id, external_logger, **kwargs):
        logger = kwargs.get("logger", None)
        if not logger:
            logger = cls(diff_id=diff_id, external_logger=external_logger)
        return logger


def update(
    benchmark,
    test,
    external_logger=None,
    diff_id=None,
    avoid_inner_order=True,
    **kwargs,
):
    """Compare first and then update according to the delta"""
    logger = DictCompareLogger.init_logger(diff_id, external_logger, **kwargs)
    kwargs["logger"] = logger

    diffs = compare(benchmark, test, avoid_inner_order=avoid_inner_order, **kwargs)
    logger.info(f"diffs = {diffs}")
    changes = get_dict_to_update(diffs=diffs, benchmark=benchmark, test=test, **kwargs)
    merge_dicts(test, changes)
    logger.summary(changes)
    return changes


def compare(
    benchmark: dict,
    test: dict,
    key: str = None,
    avoid_inner_order: bool = False,
    external_logger=None,
    diff_id=None,
    **kwargs,
):
    """Compare between two dictionaries"""
    logger = DictCompareLogger.init_logger(diff_id, external_logger, **kwargs)
    kwargs["logger"] = logger

    diffs = DictDiff()
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


def compare_with_reference(reference, original, updated, **kwargs):
    # Get changes between dict and its original state
    diffs_original = compare(benchmark=original, test=updated, **kwargs)

    # return all changed values to other than the default
    changes = set()
    # iterate over the modified keys
    for mapped_keys, (_, new_value) in diffs_original.modified.items():
        # get reference value
        reference_value = get_nested_value(
            mapped_keys, reference, default=NOT_FOUND, **kwargs
        )
        if new_value != reference_value:
            # if they are different, it is a change
            changes.add(mapped_keys)
    return changes


class DictDiff:
    def __init__(self, added=None, removed=None, modified=None):
        self.added = added or {}
        self.removed = removed or {}
        self.modified = modified or {}

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
        return str(self.changes)

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
        if get_nested_value(mapped_key, test, default=NOT_FOUND, **kwargs) is NOT_FOUND:
            added[bench_key] = benchmark[bench_key]
    return DictDiff(added=added)


def removed_keys(benchmark: Dict[str, Any], test: Dict[str, Any], **kwargs):
    test_keys = get_valid_mapped_keys(test, **kwargs)
    bench_keys = mapped_to_bench_keys(test_keys, **kwargs)
    removed = {}
    for bench_key, mapped_key in zip(bench_keys, test_keys):
        if (
            get_nested_value(bench_key, benchmark, default=NOT_FOUND, **kwargs)
            is NOT_FOUND
        ):
            removed[mapped_key] = get_nested_value(
                mapped_key,
                test,
                default=AssertionError(f"{mapped_key} is not found in test"),
                **kwargs,
            )
    return DictDiff(removed=removed)


def modified_keys(shared, avoid_inner_order, key: str = None, **kwargs):
    modify_diff = DictDiff()

    for (bench_key, bench_value, mapped_keys, test_value) in shared:
        bench_value = fix_key(bench_key, bench_value, **kwargs)
        test_value = fix_key(mapped_keys, test_value, **kwargs)

        if avoid_inner_order and all(
            isinstance(v, COLLECTION_VAR) for v in (bench_value, test_value)
        ):
            compare_bench_value = value_of(bench_value)
            compare_test_value = value_of(test_value)
        else:
            compare_bench_value = bench_value
            compare_test_value = test_value

        if compare_bench_value != compare_test_value:
            if all(isinstance(v, dict) for v in (bench_value, test_value)):
                # recursively
                kwargs["recursive"] = True
                diffs = compare(
                    bench_value,
                    test_value,
                    key=bench_key,
                    avoid_inner_order=avoid_inner_order,
                    **kwargs,
                )
            else:
                diffs = DictDiff(modified={bench_key: (bench_value, test_value)})
            modify_diff.update(diffs, key=key)
    return modify_diff


def get_dict_to_update(diffs: DictDiff, benchmark: dict, test: dict, **kwargs):
    logger = kwargs.get("logger")
    delta = {}

    for bench_key, mapped_keys in iterator(diffs.added, **kwargs):
        entry = convert_to_nested_dicts(
            mapped_keys,
            value=get_nested_value(
                bench_key,
                diffs.added,
                default=AssertionError(f"{bench_key} is not found in added"),
                **kwargs,
            ),
        )
        logger.info(f"Add a new benchmark key: {entry}")
        merge_dicts(delta, entry)

    # fields that are allowed to be changed. If a modification field was changed then we keep it,
    # else we restore it. This will allow us to keep user modified changes ot specific fields
    # and to revert unofficially changes.

    modification_fields = set(kwargs.get("modification_fields", []))

    for bench_key, mapped_keys in iterator(diffs.modified, **kwargs):
        bench_value = get_nested_value(
            bench_key,
            benchmark,
            default=AssertionError(f"{bench_key} is not found in benchmark"),
            **kwargs,
        )
        mapped_value = get_nested_value(
            mapped_keys,
            test,
            default=AssertionError(f"{mapped_keys} is not found in test"),
            **kwargs,
        )

        values = f"benchmark='{bench_value}', existing='{mapped_value}'"

        must_modify = all(k not in modification_fields for k in mapped_keys)
        if mapped_value is NOT_FOUND or must_modify:
            # either the value is a new one or it was modified unofficially and should be restored
            value = bench_value
            modify_type = "modify key [benchmark]"
        else:
            # value was officially changed so we add it to the benchmark values
            type_bench = type(bench_value)
            type_mapped = type(mapped_value)
            if type_bench != type_mapped:
                modify_type = "modify key [types mismatch: take benchmark]"
                value = bench_value
            elif type_bench not in COLLECTION_VAR:
                # Take only user defined value
                modify_type = "modify key [user-modified]"
                value = mapped_value
            else:
                # combine both benchmark and user defined changes
                modify_type = "modify key [benchmark & user-modified]"
                value = list(set(mapped_value).union(set(bench_value)))

        nested_dict_to_update = convert_to_nested_dicts(mapped_keys, value=value)
        logger.info(f"{modify_type}: '{nested_dict_to_update}'. Values: [{values}]")
        merge_dicts(delta, nested_dict_to_update)
    return delta


def get_column_mapping(**kwargs):
    column_mapping = kwargs.get('column_mapping', {})
    mapping = column_mapping.get("map", {})
    if kwargs.get("recursive"):
        if not column_mapping.get("inner_key_validity"):
            mapping = {}
    return mapping


def bench_to_mapped_keys(bench_keys, **kwargs):
    column_mapping = get_column_mapping(**kwargs)
    return tuple(column_mapping.get(o, o) for o in bench_keys)


def mapped_to_bench_keys(mapped_keys, **kwargs):
    column_mapping = get_column_mapping(**kwargs)
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


def merge_dicts(orig_dict, new_dict):
    """Merge two dict by keeping both keys-values"""
    for key, val in new_dict.items():
        if isinstance(val, dict):
            orig_dict[key] = merge_dicts(orig_dict.get(key, {}) or {}, val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict


def fix_key(keys, value, **kwargs):
    fix_funcs = kwargs.get("fix_funcs", {})
    if not fix_funcs:
        return value
    for key in tuplize(keys):
        for func in fix_funcs.get(key, []):
            try:
                value = func(value)
            except (Exception,):
                logger = kwargs.get("logger")
                logger.error(f"Failed to fix key '{key}={value}' using '{func}'")
                break
    return value


def get_shared_keys(benchmark, test, **kwargs):
    """Get shared keys between two dictionaries"""
    shared = []
    for bench_key, mapped_keys in iterator(benchmark, **kwargs):
        if key_to_ignore(bench_key, **kwargs):
            continue
        bench_value = get_nested_value(
            bench_key, benchmark, default=NOT_FOUND, **kwargs
        )
        mapped_value = get_nested_value(mapped_keys, test, default=NOT_FOUND, **kwargs)
        if NOT_FOUND not in (mapped_value, bench_value):
            # take only keys in both dicts
            shared.append((bench_key, bench_value, mapped_keys, mapped_value))
    return shared


def key_to_ignore(key, **kwargs):
    return key.startswith("_") or key in kwargs.get("ignore_keys", [])


def value_of(item: Union[COLLECTION_VAR]):
    """Align value of given collection to a sorted list"""
    try:
        return sorted(list(set(item)))
    except TypeError:
        return item


def get_nested_value(key, _dict, default, **kwargs):
    column_mapping = kwargs.get('column_mapping', {})
    generic_key = column_mapping.get("generic_key", [])
    keys = [*generic_key]
    if isinstance(key, COLLECTION_VAR):
        keys.extend(key)
    else:
        keys.append(key)

    for _key in [key, tuple(keys)]:
        try:
            # try a direct dict-key
            return _dict[_key]
        except KeyError:
            # try chained keys traverse
            _test = deepcopy(_dict)
            try:
                for k in _key:
                    _test = _test[k]
                return _test
            except KeyError:
                pass
    # default handling
    if isinstance(default, Exception):
        raise default
    return default


def iterator(collection, **kwargs):
    column_mapping = get_column_mapping(**kwargs)
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
            if isinstance(v, dict):
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
