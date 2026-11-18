"""生成阶段报告：既有报告保留，新报告标明指标与可比较人群的变化。"""
import json
from datetime import datetime
from .evidence import receive
from .independence import stage_metrics, population

METRICS=('participants','withdrawn','planned_sessions','sessions','independent_sessions','assisted_sessions','independent_rate','usable_minutes','independent_per_usable_hour')

def _previous(db,revision,received_at):
    marker=(datetime.fromisoformat(received_at),revision);best=None
    for rev,rec,body in db.execute("SELECT revision,received_at,body FROM documents WHERE kind='report'"):
        if rev==revision:continue
        m=(datetime.fromisoformat(rec),rev)
        if m<marker and (best is None or m>best[0]):best=(m,rev,json.loads(body))
    return (best[1],best[2]) if best else None

def _union(pop,key):
    out=set()
    for v in pop.values():out.update(v[key])
    return out

def _diff(prev,current):
    changes={'compared_to':None,'metric_changes':[],'population_changes':{}}
    if not prev:return changes
    rev,body=prev
    changes['compared_to']=rev
    old={s['stage']:s for s in body.get('stages',[])}
    for st in current['stages']:
        o=old.get(st['stage'])
        if not o:
            changes['metric_changes'].append({'stage':st['stage'],'metric':'stage','previous':None,'current':'新增阶段'})
            continue
        for key in METRICS:
            if o.get(key)!=st.get(key):
                changes['metric_changes'].append({'stage':st['stage'],'metric':key,'previous':o.get(key),'current':st.get(key)})
    for stage in sorted(set(old)-{s['stage'] for s in current['stages']}):
        changes['metric_changes'].append({'stage':stage,'metric':'stage','previous':'既有阶段','current':None})
    oldpop=body.get('population',{});newpop=current['population']
    common=set(oldpop)&set(newpop)
    old_sessions=_union(oldpop,'sessions');new_sessions=_union(newpop,'sessions')
    changes['population_changes']={
        'participants_added':sorted(set(newpop)-set(oldpop)),
        'participants_removed':sorted(set(oldpop)-set(newpop)),
        'participants_withdrawn':sorted(p for p in common if newpop[p]['withdrawn'] and not oldpop[p]['withdrawn']),
        'sessions_added':sorted(new_sessions-old_sessions),
        'sessions_removed':sorted(old_sessions-new_sessions),
        'independence_changed':sorted((_union(oldpop,'independent')^_union(newpop,'independent'))&old_sessions&new_sessions),
    }
    return changes

def generate(db,known_at,revision,received_at=None):
    """按 known_at 生成报告并作为不可覆盖版本存入链中。"""
    received_at=received_at or known_at
    metrics=stage_metrics(db,known_at)
    current={'known_at':known_at,'stages':metrics['stages'],'pending_sessions':metrics['pending_sessions'],'population':population(db,known_at)}
    current['changes']=_diff(_previous(db,revision,received_at),current)
    receive(db,{'kind':'report','id':'stage-report','revision':revision,'received_at':received_at,'payload':current})
    return {'revision':revision,**current}

def reports(db):
    """列出所有保留的阶段报告版本。"""
    out=[]
    for rev,rec,body in db.execute("SELECT revision,received_at,body FROM documents WHERE kind='report' ORDER BY received_at,revision"):
        out.append({'revision':rev,'received_at':rec,'payload':json.loads(body)})
    return out
