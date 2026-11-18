"""把会话、校准、辅助、不可用与退出记录连成可核对的链；撤回只影响其后的判定。"""
from collections import defaultdict
from .evidence import at

REASONS=('calibration','fatigue','device_down','caregiver_proxy')

def retractions(db,known_at):
    out=set()
    for r in at(db,'retraction',known_at):
        p=r['payload']
        out.add((p['target_kind'],p['target_id']))
    return out

def valid(db,kind,known_at):
    """截至 known_at 未被撤回的某类资料最新版本。"""
    gone=retractions(db,known_at)
    return [r for r in at(db,kind,known_at) if (kind,r['id']) not in gone]

def by_session(rows):
    out=defaultdict(list)
    for r in rows:out[r['payload']['session']].append(r)
    return out

def latest_calibration(db,known_at):
    """每个会话取最近收到的校准判定，研究人员可通过新版本改判。"""
    picked={}
    for r in valid(db,'calibration',known_at):
        s=r['payload']['session']
        if s not in picked or (r['received_at'],r['revision'])>(picked[s]['received_at'],picked[s]['revision']):picked[s]=r
    return picked
