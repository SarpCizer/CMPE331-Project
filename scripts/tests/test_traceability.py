"""Reject broken or ambiguous criterion-to-assertion evidence."""
import json
import re
import unittest
from unittest.mock import patch

import criterion_assertions as mapping


class TraceabilityTests(unittest.TestCase):
    def test_all_approved_criteria_have_a_concrete_immutable_assertion(self):
        saved=json.loads((mapping.ROOT/'docs/tests/coverage/traceability.json').read_text(encoding='utf-8'))
        rows,count=mapping.build(saved['assertion_revision'])
        self.assertEqual(rows,saved['rows'])
        self.assertEqual(count,saved['unique_physical_acceptance_ids'])
        expected=set()
        for path in (mapping.ROOT/'docs/requirements').glob('US-*.md'):
            criteria=re.findall(r'^\d+\. Given .+$',path.read_text(encoding='utf-8'),re.MULTILINE)
            expected.update((path.stem,f'AC-{i:02}') for i in range(1,len(criteria)+1))
        self.assertEqual(expected,{(r['requirement'],r['criterion']) for r in rows if r['requirement'].startswith('US-')})
        self.assertEqual({r['requirement'] for r in rows if r['requirement'].startswith('NFR')},{f'NFR-{i:02}' for i in range(1,10)})

    def test_duplicate_physical_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            mapping.unique_ids("test('US-01-T01 first');\ntest('US-01-T01 second');")

    def test_deleted_assertion_cannot_silently_remain_mapped(self):
        with patch.object(mapping,'git',return_value=b'test source'), patch.object(mapping.Path,'read_text',return_value='test source'):
            with self.assertRaisesRegex(ValueError,'Missing assertion'):
                mapping.resolve('test.mjs','<module>','assert.equal(removed, true)','a'*40)

    def test_changed_test_source_cannot_use_old_assertion_links(self):
        with patch.object(mapping,'git',return_value=b'old'), patch.object(mapping.Path,'read_text',return_value='new'):
            with self.assertRaisesRegex(ValueError,'differs'):
                mapping.resolve('test.mjs','<module>','old','a'*40)


if __name__=='__main__': unittest.main()
