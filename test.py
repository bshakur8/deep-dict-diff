import unittest
from copy import deepcopy

import dict_compare

EVENT_DEF_EXTRA_ARGS = {
    "column_mapping": dict(
        map={
            "action": "action_definitions",
            "alarm": "alarm_definitions",
            "text": "event_message",
        },
        inner_key_validity=False,
        generic_key=["metadata"],
    ),
    "fix_funcs": {"event_type": [str.upper]},
    "ignore_keys": ["id"],
}

event_def_cluster = {
    "action": {
        "alarm_only": False,  # added
        "new_action_key_added": 15,  # added
        "call_home": {"subject": "Cluster Upgrade state - {new_value}"},
    },  # wasn't changed
    "alarm": {
        "severity": "CRITICAL",  # modified
        "trigger_off": ["DONE", "NEW_CASE"],  # modified
        "trigger_on": ["ROLLBACK", "SHOULD_ADDED"],
    },  # modified
    "event_type": "object_modified",  # wasn't changed
    "name": "NEW_NAME",  # modified
    "object_type": "Cluster",  # wasn't changed
    "property": "upgrade_state",  # wasn't changed
    "cooldown": 1441,  # modifed
    "text": "AM A new test message",  # modified
    "totally_distinct_key": 1,  # added
    "extra_validators": {
        "check_ha_events": {"timeframe": "15m", "delay": 1}
    },  # delay was modified
}

exist_event_def_cluster = {
    "_state": "1234",
    "action_definitions": {
        "call_home": {"subject": "Cluster Upgrade state - {new_value}"}
    },
    "alarm_definitions": {
        "severity": "MAJOR",  # modify
        "trigger_off": ["DONE", "ANOTHER_CASE"],  # modify
        "trigger_on": ["ROLLBACK"],
    },  # modified
    "cooldown": None,  # modified
    "disable_actions": False,  # added
    "event_message": "Cluster {obj} {property} changed from {old_value} to {new_value}",  # change 5
    "event_type": "OBJECT_MODIFIED",
    "id": 14,
    "extra_validators": {
        "check_ha_events": {"timeframe": "15m", "delay": 666}
    },  # change 6
    "internal": False,
    "metadata": {
        "changed_fields": [
            ['alarm', 'severity'],
            ['alarm', 'trigger_off'],
            ['disable_actions'],
        ],
        "action": {"call_home": {"subject": "Cluster Upgrade state - {new_value}"}},
        "alarm": {
            "severity": "CRITICAL",
            "trigger_off": ["DONE"],
            "trigger_on": ["ROLLBACK"],
        },
        "event_type": "object_modified",
        "name": "CLUSTER_UPGRADE_STATE_OBJECT_MODIFIED",
        "object_type": "Cluster",
        "property": "upgrade_state",
        "text": "Cluster {obj} {property} changed from {old_value} to {new_value}",  # change 7
        "user_modified": True,
    },
    "name": "CLUSTER_UPGRADE_STATE_OBJECT_MODIFIED",  # change 8
    "object_type": "Cluster",
}

event_def_task = {
    "_state": "<django.db.models.base.ModelState at 0x7fb859960898>",
    "action_definitions": {
        "call_home": {
            "subject": "[MAJOR] - Task {obj} {property} changed from {old_value} to {new_value}"
        }
    },
    "alarm_definitions": {
        "extra_validators": {
            "allowlist": {
                "allowlist": [
                    "add_cnode",
                    "remove_cnode",
                    "add_dbox",
                    "remove_dbox",
                    "optane_nvram_upgrade",
                    "ssd_upgrade",
                ],
                # 'param': 'name'
            }
        },
        "severity": "MAJOR",
        "time_to_live": "30m",
        "trigger_on": ["FAILED", "TIMEOUT"],
    },
    "cooldown": None,
    "disable_actions": False,
    "event_message": "{obj} activity {property} changed from {old_value} to {new_value}",
    "event_type": "OBJECT_MODIFIED",
    "id": 167,
    "internal": False,
    "metadata": {"changed_fields": [], "property": "state", "user_modified": False},
    "name": "TASK_STATE_CHANGED",
    "object_type": "Task",
}

exist_event_def_task = {
    "_state": "<django.db.models.base.ModelState at 0x7fb859960898>",
    "action_definitions": {
        "call_home": {
            "subject": "[MAJOR] - Task {obj} {property} changed from {old_value} to {new_value}"
        }
    },
    "alarm_definitions": {
        "extra_validators": {
            "allowlist": {
                "allowlist": [
                    "add_cnode",
                    "remove_cnode",
                    "add_dbox",
                    "remove_dbox",
                    "optane_nvram_upgrade",
                    "ssd_upgrade",
                ],
                "param": "name",
            }
        },
        "severity": "MAJOR",
        "time_to_live": "30m",
        "trigger_on": ["FAILED", "TIMEOUT"],
    },
    "cooldown": None,
    "disable_actions": False,
    "event_message": "{obj} activity {property} changed from {old_value} to {new_value}",
    "event_type": "OBJECT_MODIFIED",
    "id": 167,
    "internal": False,
    "metadata": {"changed_fields": [], "property": "state", "user_modified": False},
    "name": "TASK_STATE_CHANGED",
    "object_type": "Task",
}

exist_event_def_task_changed = {
    "_state": "<django.db.models.base.ModelState at 0xsomefake12345>",
    "action_definitions": {
        "call_home": {
            "subject": "[MAJOR] - Task {obj} {property} changed from {old_value} to {new_value}"
        }
    },
    "alarm_definitions": {
        "extra_validators": {
            "allowlist": {
                "allowlist": [
                    "add_cnode",
                    "remove_cnode",
                    "add_dbox",
                    "remove_dbox",
                    "optane_nvram_upgrade",
                    "ssd_upgrade",
                ],
                "param": "name",
            }
        },
        "severity": "MAJOR",
        "time_to_live": "30m",
        "trigger_on": ["FAILED", "TIMEOUT"],
    },
    "cooldown": None,
    "disable_actions": False,
    "event_message": "{obj} activity {property} changed from {old_value} to {new_value}",
    "event_type": "OBJECT_MODIFIED",
    "id": 167,
    "internal": False,
    "metadata": {"changed_fields": [], "property": "state", "user_modified": False},
    "name": "TASK_STATE_CHANGED",
    "object_type": "Task",
}

ad_new = {
    "alarm": {
        "severity": "MAJOR",
        "trigger_off": ["NOT_A_MEMBER", "JOINED"],
        "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
    },
    "event_type": "object_modified",
    "name": "ACTIVE_DIRECTORY_STATE",
    "object_type": "ActiveDirectory",
    "property": "state",
    "text": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
    "user_modified": False,
    "colldown": 30,
}

ad_old = {
    "_state": "<django.db.models.base.ModelState at 0x7ff95e2bb860>",
    "action_definitions": None,
    "alarm_definitions": {
        "severity": "MAJOR",
        "trigger_off": ["NOT_A_MEMBER", "JOINED"],
        "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
    },
    "cooldown": None,
    "disable_actions": False,
    "event_message": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
    "event_type": "OBJECT_MODIFIED",
    "id": 170,
    "internal": False,
    "metadata": {"changed_fields": [], "property": "state", "user_modified": False},
    "name": "ACTIVE_DIRECTORY_STATE",
    "object_type": "ActiveDirectory",
}

event_def = {
    "alarm": {
        "severity": "MAJOR",
        "trigger_off": ["CLUSTERED"],
        "trigger_on": ["DEGRADED"],
    },
    "event_type": "object_modified",
    "name": "VMS_STATE_OBJECT_MODIFIED",
    "property": "state",
    "text": "{obj} {property} changed from {old_value} to {new_value}",
    "user_modified": False,
}

event_def_dict = {
    "_state": "<django.db.models.base.ModelState at 0x7fa830141320>",
    "alarm_definitions": {},
    "event_message": {},
    "event_type": "OBJECT_MODIFIED",
    "id": 1,
    "metadata": {
        "alarm": {
            "severity": "MAJOR",
            "trigger_off": ["CLUSTERED"],
            "trigger_on": ["DEGRADED"],
        },
        "event_type": "object_modified",
        "name": "VMS_STATE_OBJECT_MODIFIED",
        "property": "state",
        "text": "{obj} {property} changed from {old_value} to {new_value}",
        "user_modified": False,
    },
    "name": "VMS_STATE_OBJECT_MODIFIED",
}

bundle = {
    "event_type": "object_modified",
    "name": "SUPPORT_BUNDLE_STATE_CHANGED",
    "property": "popo",
    "enabled": True,
    "text": "SupportBundle {obj} {property} changed from {old_value} to {new_value}",
    "user_modified": False,
}

bundle_dict = {
    "_state": "<django.db.models.base.ModelState at 0x7fa8300c3f98>",
    "action_definitions": {},
    "alarm_definitions": {},
    "cooldown": None,
    "disable_actions": False,
    "event_message": "SupportBundle {obj} {property} changed from {old_value} to {new_value}",
    "event_type": "OBJECT_MODIFIED",
    "id": 172,
    "internal": False,
    "metadata": {
        "event_type": "object_modified",
        "name": "SUPPORT_BUNDLE_STATE_CHANGED",
        "property": "state",
        "enabled": False,
        "text": "SupportBundle {obj} {property} changed from {old_value} to {new_value}",
        "user_modified": False,
        "changed_fields": ["enabled"],
    },
    "name": "SUPPORT_BUNDLE_STATE_CHANGED",
    "object_type": "SupportBundle",
}


class TestDictCompare(unittest.TestCase):
    def test_compare(self):
        diffs = dict_compare.compare(
            benchmark=exist_event_def_task_changed,
            test=exist_event_def_task,
            **EVENT_DEF_EXTRA_ARGS
        )
        self.assertNotIn("_state", diffs.modified)

    def test_metadata(self):
        test_event_def = {
            "alarm": {
                "severity": "MAJOR",
                "trigger_off": [False],
                "trigger_off_text": "Quota {obj} is below the soft limit",
                "trigger_on": [True],
                "trigger_on_text": "Quota {obj} soft limit exceeded",
            },
            "changed_fields": [["alarm", "severity"]],
            "enabled": True,
            "event_type": "object_modified",
            "name": "QUOTA_SOFT_EXCEEDED",
            "property": "soft_exceeded",
            "text": "Quota {obj} soft limit exceeded: {new_value}",
            "user_modified": True,
        }

        original = {
            "alarm": {
                "severity": "MAJOR",
                "trigger_off": [False],
                "trigger_off_text": "Quota {obj} is below the soft limit",
                "trigger_on": [True],
                "trigger_on_text": "Quota {obj} soft limit exceeded",
            },
            "changed_fields": [["alarm", "severity"]],
            "enabled": False,
            "event_type": "object_modified",
            "name": "QUOTA_SOFT_EXCEEDED",
            "property": "soft_exceeded",
            "text": "Quota {obj} soft limit exceeded: {new_value}",
            "user_modified": True,
        }

        res = dict_compare.compare(benchmark=original, test=test_event_def)
        self.assertEqual(res.modified, {("enabled",): (False, True)})

    def test_bundle(self):
        benchmark = deepcopy(bundle)
        test = deepcopy(bundle_dict)

        kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)
        kwargs['changed_fields'] = test['metadata']['changed_fields']
        changes = dict_compare.update(benchmark, test, **kwargs)
        self.assertEqual(
            changes,
            {"property": "popo", "enabled": False},
        )

    def test_None_values(self):
        self.assertEqual(event_def_dict["alarm_definitions"], {})
        self.assertEqual(event_def_dict["event_message"], {})

        benchmark = deepcopy(event_def)
        test = deepcopy(event_def_dict)
        changes = dict_compare.update(benchmark, test, **EVENT_DEF_EXTRA_ARGS)
        self.assertEqual(test["alarm_definitions"]["severity"], "MAJOR")
        self.assertEqual(test["alarm_definitions"]["trigger_off"], ["CLUSTERED"])
        self.assertEqual(test["alarm_definitions"]["trigger_on"], ["DEGRADED"])
        self.assertEqual(
            test["event_message"],
            "{obj} {property} changed from {old_value} to {new_value}",
        )

    def test_ad(self):
        benchmark = deepcopy(ad_new)
        test = deepcopy(ad_old)
        changes = dict_compare.update(benchmark, test, **EVENT_DEF_EXTRA_ARGS)
        self.assertEqual(changes, {"colldown": 30})

    def test_totally_different_dicts(self):
        benchmark = deepcopy(event_def_task)
        test = deepcopy(event_def_cluster)
        dict_compare.update(benchmark, test, **EVENT_DEF_EXTRA_ARGS)

    def test_same_dict(self):
        benchmark = deepcopy(event_def_task)
        test = deepcopy(event_def_task)

        dict_compare.update(benchmark, test, **EVENT_DEF_EXTRA_ARGS)
        self.assertEqual(benchmark, test)

    def test_diff_task(self):
        benchmark = deepcopy(event_def_task)
        test = deepcopy(exist_event_def_task)
        dict_compare.update(benchmark, test, **EVENT_DEF_EXTRA_ARGS)

    def test_modify_types(self):
        benchmark = deepcopy(event_def_cluster)
        test = deepcopy(exist_event_def_cluster)

        kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)
        kwargs['changed_fields'] = test['metadata']['changed_fields']
        changes = dict_compare.update(benchmark, test, avoid_inner_order=True, **kwargs)
        self.assertEqual(test["alarm_definitions"]["severity"], "MAJOR")
        # combine benchmark and user-defined values
        for trigger_off_value in {"NEW_CASE", "ANOTHER_CASE", "DONE"}:
            self.assertIn(trigger_off_value, test["alarm_definitions"]["trigger_off"])

        for trigger_on_value in {"SHOULD_ADDED", "ROLLBACK"}:
            self.assertIn(trigger_on_value, test["alarm_definitions"]["trigger_on"])

        self.assertEqual(test["cooldown"], 1441)
        self.assertEqual(
            benchmark["extra_validators"]["check_ha_events"]["timeframe"], "15m"
        )
        self.assertEqual(
            test["extra_validators"]["check_ha_events"]["timeframe"], "15m"
        )
        self.assertEqual(test["extra_validators"]["check_ha_events"]["delay"], 1)
        self.assertEqual(
            test["name"], "NEW_NAME"
        )  # name shouldn't be modified - we restore it!
        self.assertEqual(test["totally_distinct_key"], 1)

    def test_1(self):
        benchmark = {
            "action": {
                "alarm_only": True,  # change 1
                "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                "on_trigger_off": True,
            },
            "alarm": {
                "severity": "CRITICAL",  # change 2
                "trigger_off": ["ONLINE"],
                "trigger_on": ["FAILED", "FAILING"],
            },
            "event_type": "object_modified",
            "enabled": False,  # change 3
            "name": "CLUSTER_STATE_OBJECT_MODIFIED",  # change 4
            "property": "state",
            "text": "Cluster {obj} {property} changed from {old_value} to {new_value}",
        }

        event_def_dict_ = {
            "_state": "<django.db.models.base.ModelState at 0x7eff3042add8>",
            "action_definitions": {
                "alarm_only": False,  # modified
                "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                "on_trigger_off": True,
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "alarm_definitions": {
                "severity": "MINOR",  # modified
                "trigger_off": ["ONLINE"],
                "trigger_on": ["FAILED", "FAILING"],
            },
            "cooldown": None,
            "disable_actions": False,
            "event_message": "Cluster {obj} {property} changed from {old_value} to {new_value}",
            "event_type": "OBJECT_MODIFIED",
            "id": 2,
            "internal": False,
            "metadata": {
                "action": {
                    "alarm_only": True,
                    "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                    "on_trigger_off": True,
                },
                "alarm": {
                    "severity": "CRITICAL",
                    "trigger_off": ["ONLINE"],
                    "trigger_on": ["FAILED", "FAILING"],
                },
                "event_type": "object_modified",
                "name": "CLUSTER_STATE_OBJECT_MODIFIED",
                "property": "state",
                "text": "Cluster {obj} {property} changed from {old_value} to {new_value}",
                "enabled": True,  # modified
                "user_modified": True,
                "changed_fields": [
                    ['enabled'],
                    ['alarm', 'severity'],
                    ['action', 'alarm_only'],
                ],
            },
            "name": "CLUSTER_STATE_OBJECT_MODIFIED_11111111111111111",  # restore! because name is not supposed to change
            "object_type": "Cluster",
        }
        kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)
        kwargs['changed_fields'] = event_def_dict_['metadata']['changed_fields']
        id_ = "VAST_OBJ_TYPE: event_name=EVENT_NAME12"
        changes = dict_compare.update(
            benchmark=benchmark, test=event_def_dict_, diff_id=id_, **kwargs
        )
        self.assertEqual(
            changes,
            {
                "action_definitions": {"alarm_only": False},
                "alarm_definitions": {"severity": "MINOR"},
                "enabled": True,
                "name": "CLUSTER_STATE_OBJECT_MODIFIED",
            },
        )
        # verify update
        self.assertFalse(event_def_dict_["action_definitions"]["alarm_only"])
        self.assertEqual(event_def_dict_["alarm_definitions"]["severity"], "MINOR")
        self.assertTrue(event_def_dict_["metadata"]["enabled"])
        self.assertEqual(event_def_dict_["name"], "CLUSTER_STATE_OBJECT_MODIFIED")

    def test_2(self):
        original = {
            "action_definitions": {
                "alarm_only": True,
                "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                "on_trigger_off": True,
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "alarm_definitions": {
                "severity": "MAJOR",
                "trigger_off": ["ONLINE"],
                "trigger_on": ["FAILED", "FAILING"],
            },
            "cooldown": None,
            "disable_actions": False,
            "event_message": "Cluster {obj} {property} changed from {old_value} to {new_value}",
            "event_type": "OBJECT_MODIFIED",
            "internal": False,
            "name": "CLUSTER_STATE_OBJECT_MODIFIED",
            "object_type": "Cluster",
        }

        event_def_dict_ = {
            "action_definitions": {
                "alarm_only": False,
                "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                "on_trigger_off": True,
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "alarm_definitions": {
                "severity": "MINOR",
                "trigger_off": ["ONLINE"],
                "trigger_on": ["FAILED", "FAILING"],
            },
            "cooldown": None,
            "disable_actions": True,
            "event_message": "Cluster {obj} {property} changed from {old_value} to {new_value}",
            "event_type": "OBJECT_MODIFIED",
            "internal": False,
            "name": "CLUSTER_STATE_OBJECT_MODIFIED",
            "object_type": "Cluster",
        }

        diff_kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)
        diffs = dict_compare.compare(
            benchmark=original, test=event_def_dict_, **diff_kwargs
        )
        expected = {
            ("action_definitions", "alarm_only"): (True, False),
            ("alarm_definitions", "severity"): ("MAJOR", "MINOR"),
            ("disable_actions",): (False, True),
        }

        self.assertEqual(diffs.modified, expected)

    def test_3(self):
        defaults = {
            "action": {
                "alarm_only": True,
                "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                "on_trigger_off": True,
            },
            "alarm": {
                "severity": "MINOR",
                "trigger_off": ["ONLINE"],
                "trigger_on": ["FAILED", "FAILING"],
            },
            "event_type": "object_modified",
            "name": "CLUSTER_STATE_OBJECT_MODIFIED",
            "property": "state",
            "text": "Cluster {obj} {property} changed from {old_value} to {new_value}",
        }

        event_def_dict_ = {
            "action_definitions": {
                "alarm_only": False,
                "call_home": {"subject": "[CRITICAL] - Cluster Failure"},
                "on_trigger_off": True,
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "alarm_definitions": {
                "severity": "MINOR",
                "trigger_off": ["ONLINE"],
                "trigger_on": ["FAILED", "FAILING"],
            },
            "cooldown": None,
            "disable_actions": True,
            "event_message": "Cluster {obj} {property} changed from {old_value} to {new_value}",
            "event_type": "OBJECT_MODIFIED",
            "internal": False,
            "name": "CLUSTER_STATE_OBJECT_MODIFIED",
            "object_type": "Cluster",
        }

        diff_kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)
        diffs = dict_compare.compare(benchmark=event_def_dict_, test=event_def_dict_)
        self.assertEqual(diffs.modified, {})
        self.assertEqual(diffs.added, {})
        self.assertEqual(diffs.removed, {})

        diffs = dict_compare.compare(
            benchmark=defaults, test=event_def_dict_, **diff_kwargs
        )
        self.assertEqual(diffs.added, {("property",): "state"})
        self.assertEqual(diffs.modified, {("action", "alarm_only"): (True, False)})

    def test_4(self):
        original = {
            "_state": "<django.db.models.base.ModelState at 0x7f5a1d1c6c18>",
            "action_definitions": {
                "alarm_only": False,  # 2nd change
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "alarm_definitions": {
                "severity": "MAJOR",
                "trigger_off": ["NOT_A_MEMBER", "JOINED"],
                "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
            },
            "cooldown": None,
            "disable_actions": True,  # 1st change
            "event_message": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
            "event_type": "OBJECT_MODIFIED",
            "id": 173,
            "internal": False,
            "metadata": {
                "alarm": {
                    "severity": "MAJOR",
                    "trigger_off": ["NOT_A_MEMBER", "JOINED"],
                    "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
                },
                "changed_fields": [["disable_actions"], ["action", "alarm_only"]],
                "event_type": "object_modified",
                "name": "ACTIVE_DIRECTORY_STATE",
                "property": "state",
                "text": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
                "user_modified": True,
            },
            "name": "ACTIVE_DIRECTORY_STATE",
            "object_type": "ActiveDirectory",
        }

        defaults = {
            "alarm": {
                "severity": "MAJOR",
                "trigger_off": ["NOT_A_MEMBER", "JOINED"],
                "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
            },
            "action": {"alarm_only": True},
            "event_type": "object_modified",
            "name": "ACTIVE_DIRECTORY_STATE",
            "property": "state",
            "text": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
        }

        event_def_dict_ = {
            "_state": "<django.db.models.base.ModelState at 0x7f5a1d1c6c18>",
            "action_definitions": {
                "alarm_only": True,  # back to default
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "alarm_definitions": {
                "severity": "MAJOR",  # still a change
                "trigger_off": ["NOT_A_MEMBER", "JOINED"],
                "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
            },
            "cooldown": None,
            "disable_actions": False,  # Keep this change
            "event_message": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
            "event_type": "OBJECT_MODIFIED",
            "id": 173,
            "internal": False,
            "metadata": {
                "alarm": {
                    "severity": "MAJOR",
                    "trigger_off": ["NOT_A_MEMBER", "JOINED"],
                    "trigger_on": ["JOINED_FAILED", "LEAVE_FAILED"],
                },
                "changed_fields": [["alarm", "severity"], ["action", "alarm_only"]],
                "event_type": "object_modified",
                "name": "ACTIVE_DIRECTORY_STATE",
                "property": "state",
                "text": "{obj} {property} changed from {old_value} to {new_value}. {obj.error_string}",
                "user_modified": True,
            },
            "name": "ACTIVE_DIRECTORY_STATE",
            "object_type": "ActiveDirectory",
        }

        diff_kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)

        diffs_original = dict_compare.compare(
            benchmark=original, test=event_def_dict_, **diff_kwargs
        )
        self.assertEqual(diffs_original.added, {})
        self.assertEqual(
            diffs_original.modified,
            (
                {
                    ("action_definitions", "alarm_only"): (False, True),
                    ("disable_actions",): (True, False),
                    ("metadata", "changed_fields"): (
                        [["disable_actions"], ["action", "alarm_only"]],
                        [["alarm", "severity"], ["action", "alarm_only"]],
                    ),
                }
            ),
        )

        diffs_defaults = dict_compare.compare(
            benchmark=defaults, test=event_def_dict_, **diff_kwargs
        )
        self.assertEqual(diffs_defaults.added, {})
        self.assertEqual(diffs_defaults.modified, {})

    def test_changed_fields(self):
        original = {
            "action_definitions": {
                "alarm_only": False,  # 2nd change
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "disable_actions": True,  # 1st change
        }
        event_def_dict_ = {
            "action_definitions": {
                "alarm_only": True,  # back to default
                "send_mail": {"recipients": []},
                "webhook": {"method": ""},
            },
            "disable_actions": False,  # Keep this change
        }
        changed_fields = [["action_definitions", "alarm_only"], ["disable_actions"]]

        diff_kwargs = deepcopy(EVENT_DEF_EXTRA_ARGS)
        ignore_keys = diff_kwargs.get("ignore_keys", [])
        ignore_keys.append("metadata")
        diff_kwargs.update({"ignore_keys": ignore_keys})
        diff_kwargs["changed_fields"] = changed_fields

        changes = dict_compare.update(
            benchmark=original, test=event_def_dict_, **diff_kwargs
        )
        self.assertFalse(event_def_dict_["disable_actions"])
        self.assertTrue(event_def_dict_["action_definitions"]["alarm_only"])

    def test_list_order(self):
        original = {"alarm_definitions": {"trigger_off": ("A", "B")}}
        event_def_dict_ = {"alarm_definitions": {"trigger_off": ("B", "A")}}

        diffs = dict_compare.compare(original, event_def_dict_, avoid_inner_order=True)
        self.assertEqual(diffs.added, {})
        self.assertEqual(diffs.removed, {})
        self.assertEqual(diffs.modified, {})

        diffs = dict_compare.compare(original, event_def_dict_, avoid_inner_order=False)
        self.assertEqual(diffs.added, {})
        self.assertEqual(diffs.removed, {})
        self.assertEqual(
            diffs.modified,
            {("alarm_definitions", "trigger_off"): (("A", "B"), ("B", "A"))},
        )

    def test_removed_key_from_benchmark(self):
        benchmark = {"A": 1}
        test = {"B": 2}
        diffs = dict_compare.update(benchmark, test, avoid_inner_order=True)
        self.assertEqual(diffs, {"A": 1})  # 'B' is not longer exists in A, remove it!

    def test_modify_type_mismatch(self):
        # same key but different value collection type,
        # should revert to the benchmark
        benchmark = {"A": [12, 3]}
        test = {"A": "branch new type"}
        diffs = dict_compare.update(
            benchmark, test, avoid_inner_order=True, changed_fields=[['A']]
        )
        self.assertEqual(diffs, benchmark)
        self.assertEqual(test, benchmark)

    def test_modify_type_collection_not_same_type(self):
        # same key and same value collection type,
        # but not all items types in value are the same. Should remain with the user modified
        benchmark = {"A": [12, 3]}
        test = {"A": ["ge", 3]}
        dict_compare.update(
            benchmark, test, avoid_inner_order=True, changed_fields=[['A']]
        )
        self.assertEqual(test['A'], ['ge', 3])

    def test_modify_deep_innder_dict(self):
        benchmark = {
            "A": {
                'A1':
                    {
                        'A11': [12, 3],
                        'A12': False,
                        'A13': {
                            'A131': ['key1', 'key2']
                        },
                     },
                'A2': 15,
                'A3': "low"
            },
            "B": "bee",
            "C": [1, 2, 3],
            "D": {
                "D1": {
                    "D12": ["one", "two"]
                },
                "D2": [1.2, -7.4]
            }
        }
        test = {
            "A": {
                'A1':
                    {
                        'A11': [12, 3],
                        'A12': True,
                        'A13': {
                            'A131': ['key1', 'key2']
                        },
                    },
                'A2': 15,
                'A3': "low"
            },           "B": "poo",
            "C": [1, 2, 3],
            "D": {
                "D1": {
                    "D12": ["one", "two"]
                },
                "D2": [1.2, -7.4]
            }
        }
        diff = dict_compare.update(
            benchmark, test, avoid_inner_order=True, changed_fields=[['A', 'A1', 'A22'], ['B']]
        )
        self.assertEqual(diff, {'A': {'A1': {'A12': False}}, "B": "poo"})
        self.assertEqual(test['B'], 'poo')


if __name__ == "__main__":
    unittest.main()
