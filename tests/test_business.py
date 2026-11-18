"""核对业务资料的当前结果及版本冲突。"""
import json
import unittest
from pathlib import Path
from neuro_trial.evidence import connect, receive
from neuro_trial.followup import stages
DATA=json.loads((Path(__file__).resolve().parents[1]/'data'/'example.json').read_text(encoding='utf-8'))
class BusinessChain(unittest.TestCase):
    def setUp(self):self.db=connect()
    def tearDown(self):self.db.close()
    def test_current_result(self):
        for item in DATA['documents']:receive(self.db,item)
        result=stages(self.db,DATA['known_at'])
        self.assertTrue(result)
        self.assertIn('completed',json.dumps(result,ensure_ascii=False))
    def test_conflicting_revision(self):
        item=DATA['documents'][0]
        receive(self.db,item)
        changed=json.loads(json.dumps(item))
        changed['payload']['conflict']=True
        with self.assertRaises(ValueError):receive(self.db,changed)
