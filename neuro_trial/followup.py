from collections import defaultdict
from .sessions import usage
def stages(db, known_at):
    groups=defaultdict(list)
    for row in usage(db,known_at):
        if 'stage' in row:groups[row['stage']].append(row)
    return [{'stage':stage,'sessions':len(items),'completed':sum(bool(x['completed']) for x in items),'observed_minutes':sum(x['minutes'] for x in items)} for stage,items in sorted(groups.items())]
