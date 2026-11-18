"""核对独立完成率、实际可用时间、退出者分母与阶段报告版本。"""
import json
import unittest
from pathlib import Path
from neuro_trial.evidence import connect, receive
from neuro_trial.independence import sessions, stage_metrics
from neuro_trial.report import generate, reports
ROOT=Path(__file__).resolve().parents[1]
BASE=json.loads((ROOT/'data'/'example.json').read_text(encoding='utf-8'))
REVISED=json.loads((ROOT/'data'/'revised.json').read_text(encoding='utf-8'))
class IndependenceChain(unittest.TestCase):
    def setUp(self):
        self.db=connect()
        for item in BASE['documents']:receive(self.db,item)
    def tearDown(self):self.db.close()
    def test_independent_excludes_assisted(self):
        rows={s['session']:s for s in sessions(self.db,BASE['known_at'])}
        self.assertTrue(rows['S1']['independent'])
        self.assertFalse(rows['S2']['independent'])
        self.assertTrue(rows['S2']['assisted'])
        self.assertEqual(rows['S2']['calibration_version'],'cal-2.1')
    def test_usable_minutes_subtract_unavailability(self):
        rows={s['session']:s for s in sessions(self.db,BASE['known_at'])}
        self.assertEqual(rows['S2']['usable_minutes'],15)
        self.assertEqual(rows['S2']['unavailable']['caregiver_proxy'],10)
        self.assertEqual(rows['S3']['unavailable']['fatigue'],8)
        self.assertEqual(rows['S3']['unavailable']['device_down'],4)
    def test_withdrawn_stays_in_denominator(self):
        metrics={s['stage']:s for s in stage_metrics(self.db,BASE['known_at'])['stages']}
        w2=metrics['week-2']
        self.assertEqual(w2['participants'],2)
        self.assertEqual(w2['withdrawn'],1)
        self.assertEqual(w2['planned_sessions'],6)
        self.assertAlmostEqual(w2['independent_rate'],2/6)
        self.assertAlmostEqual(w2['independent_per_usable_hour'],2/(56/60))
    def test_report_preserved_and_changes_marked(self):
        first=generate(self.db,BASE['known_at'],'r1')
        for item in REVISED['documents']:receive(self.db,item)
        second=generate(self.db,REVISED['known_at'],'r2')
        self.assertEqual([r['revision'] for r in reports(self.db)],['r1','r2'])
        old={s['stage']:s for s in first['stages']}
        self.assertEqual(old['week-2']['independent_sessions'],2)
        changes=second['changes']
        self.assertEqual(changes['compared_to'],'r1')
        self.assertIn('S5',changes['population_changes']['sessions_removed'])
        self.assertIn('S4',changes['population_changes']['independence_changed'])
        metrics={(c['stage'],c['metric']):c for c in changes['metric_changes']}
        self.assertEqual(metrics[('week-2','independent_sessions')]['previous'],2)
        self.assertEqual(metrics[('week-2','independent_sessions')]['current'],0)
        self.assertEqual(metrics[('week-2','independent_rate')]['current'],0)
    def test_revision_not_applied_before_received(self):
        for item in REVISED['documents']:receive(self.db,item)
        metrics={s['stage']:s for s in stage_metrics(self.db,BASE['known_at'])['stages']}
        self.assertEqual(metrics['week-2']['independent_sessions'],2)
        self.assertEqual(metrics['week-2']['sessions'],3)
    def test_report_revision_cannot_be_overwritten(self):
        generate(self.db,BASE['known_at'],'r1')
        for item in REVISED['documents']:receive(self.db,item)
        with self.assertRaises(ValueError):generate(self.db,REVISED['known_at'],'r1')
