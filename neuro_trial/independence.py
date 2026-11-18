"""按实际可用时间比较各阶段的独立完成率，中途退出者留在分母中。"""
from collections import defaultdict
from .records import valid, latest_calibration, by_session, REASONS

def _minutes(row):
    m=row['payload'].get('minutes',0)
    return m if isinstance(m,(int,float)) and m>0 else 0

def sessions(db,known_at):
    """逐会话评估：任务完成、校准有效且无人代操作，才算独立完成。"""
    people={r['id']:r for r in valid(db,'participant',known_at)}
    calib=latest_calibration(db,known_at)
    assisted=by_session(valid(db,'assistance',known_at))
    gaps=by_session(valid(db,'unavailability',known_at))
    out=[]
    for row in valid(db,'session',known_at):
        p=row['payload'];sid=row['id']
        person=people.get(p.get('person'))
        unavail=defaultdict(float)
        for g in gaps.get(sid,[]):
            reason=g['payload'].get('reason')
            if reason:unavail[reason]+=_minutes(g)
        caregiver=sum(_minutes(a) for a in assisted.get(sid,[]) if a['payload'].get('actor')=='caregiver')
        if caregiver:unavail['caregiver_proxy']+=caregiver
        minutes=_minutes(row)
        cal=calib.get(sid)
        helped=bool(assisted.get(sid))
        cal_ok=bool(cal and cal['payload'].get('valid'))
        out.append({
            'session':sid,
            'person':p.get('person'),
            'stage':person['payload'].get('stage') if person else None,
            'minutes':minutes,
            'completed':bool(p.get('completed')),
            'calibration_version':cal['payload'].get('version') if cal else None,
            'calibration_valid':cal_ok,
            'assisted':helped,
            'unavailable':dict(unavail),
            'usable_minutes':max(0.0,minutes-sum(unavail.values())),
            'independent':bool(p.get('completed')) and cal_ok and not helped,
            'source':row['digest'],
        })
    return out

def stage_metrics(db,known_at):
    """按阶段汇总：分母为入组人数×计划会话数，退出者不剔除。"""
    people=valid(db,'participant',known_at)
    plans={r['payload']['stage']:r['payload'].get('planned_sessions',0) for r in valid(db,'plan',known_at)}
    withdrawn=defaultdict(list)
    for w in valid(db,'withdrawal',known_at):withdrawn[w['payload']['person']].append(w)
    rows=sessions(db,known_at)
    by_stage=defaultdict(list);pending=[]
    for s in rows:
        (by_stage[s['stage']].append(s) if s['stage'] else pending.append(s))
    members=defaultdict(list)
    for r in people:members[r['payload'].get('stage')].append(r)
    out=[]
    for stage in sorted(set(members)|set(by_stage)):
        folks=members[stage];items=by_stage[stage]
        gone=[r['id'] for r in folks if r['id'] in withdrawn]
        if stage in plans:
            planned=plans[stage]*len(folks);source='plan'
        else:
            planned=len(items);source='observed'
        indep=[s for s in items if s['independent']]
        usable=sum(s['usable_minutes'] for s in items)
        unavail=defaultdict(float)
        for s in items:
            for k,v in s['unavailable'].items():unavail[k]+=v
        out.append({
            'stage':stage,
            'participants':len(folks),
            'withdrawn':len(gone),
            'active':len(folks)-len(gone),
            'planned_sessions':planned,
            'plan_source':source,
            'sessions':len(items),
            'independent_sessions':len(indep),
            'assisted_sessions':sum(bool(s['assisted']) for s in items),
            'independent_rate':(len(indep)/planned) if planned else None,
            'observed_minutes':sum(s['minutes'] for s in items),
            'usable_minutes':usable,
            'unavailable_minutes':{k:unavail[k] for k in sorted(unavail)},
            'independent_per_usable_hour':(len(indep)/(usable/60)) if usable else None,
        })
    return {'stages':out,'pending_sessions':[s['session'] for s in pending]}

def population(db,known_at):
    """可比较人群快照：谁在哪个阶段、哪些会话计入、哪些独立完成。"""
    rows=sessions(db,known_at)
    by_person=defaultdict(list)
    for s in rows:by_person[s['person']].append(s)
    withdrawn={w['payload']['person'] for w in valid(db,'withdrawal',known_at)}
    snap={}
    for r in valid(db,'participant',known_at):
        pid=r['id'];items=by_person.get(pid,[])
        snap[pid]={
            'stage':r['payload'].get('stage'),
            'withdrawn':pid in withdrawn,
            'sessions':sorted(s['session'] for s in items),
            'independent':sorted(s['session'] for s in items if s['independent']),
        }
    return snap
