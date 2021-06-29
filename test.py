import unittest
from pprint import pprint

from dict_compare import DictCompare


class SimpleTest(unittest.TestCase):

    def test_changed_fields(self):
        d1 = {'key1': {'severity': 'CRITICAL'},
              'key2': 'val2',
              'key3': {'key4': 'val4'}}

        d2 = {'key1': {'severity': 'MAJOR'},
              'key2': 'val2',
              'key3': {'key4': 'val4'}}

        extra_args = {'column_mapping': {},
                      'changed_fields': [['alarm', 'severity']]}

        changes = DictCompare.update(benchmark=d1, test=d2, avoid_inner_order=True, **extra_args)
        pprint(d2)


def foo():
    d1 = {'event_type': 'object_modified', 'name': 'CNODE_SLOW_CPU_DETECTED', 'property': 'slow_cpu',
          'text': 'CNode {obj} detected slow CPU speed STAMM!@!!!!!',
          'alarm': {'trigger_on': [True, 'DONE'], 'trigger_off': [False],
                    'severity': 'CRITICAL', 'trigger_off_text': 'CNode {obj} CPU speed back to normal',
                    'trigger_on_text': "STAM trigger on"}}


    changed_fields = [['alarm', 'severity']]

    d2 = {'id': 61, 'object_type': 'CNode', 'event_type': 'OBJECT_MODIFIED',
          'event_message': 'CNode {obj} detected slow CPU speed',
          'metadata': {'property': 'slow_cpu', 'user_modified': False},
          'changed_fields': [['alarm', 'severity']],
          'alarm_definitions': {'severity': 'MAJOR', 'trigger_on': [True], 'trigger_off': [False]},
          'action_definitions': None, 'disable_actions': False, 'name': 'CNODE_SLOW_CPU_DETECTED', 'internal': False,
          'cooldown': None}

    extra_args = {'column_mapping': {'action': 'action_definitions',
                                     'alarm': 'alarm_definitions',
                                     'cooldown': ('metadata', 'cooldown'),
                                     'enabled': ('metadata', 'enabled'),
                                     'internal': ('metadata', 'internal'),
                                     'minimum': ('metadata', 'minimum'),
                                     'property': ('metadata', 'property'),
                                     'text': 'event_message',
                                     'time_frame': ('metadata', 'time_frame'),
                                     'persistence': ('metadata', 'persistence'),
                                     'trigger_off_text': ('metadata', 'trigger_off_text'),
                                     'trigger_on_text': ('metadata', 'trigger_on_text')},
                  'fix_funcs': {'event_type': [str.upper]},
                  'ignore_keys': ['id', '_state'],
                  'modification_fields': ['severity',
                                          'trigger_on',
                                          'trigger_off',
                                          'webhook',
                                          'send_email',
                                          'disable_actions',
                                          'alarm_only']}

    extra_args.update({'changed_fields': changed_fields})
    # diff = DictCompare.compare(benchmark=d1, test=d2, avoid_inner_order=True, **extra_args)
    # pprint(diff)

    changes = DictCompare.update(benchmark=d1, test=d2, avoid_inner_order=True, **extra_args)
    pprint(d2)
