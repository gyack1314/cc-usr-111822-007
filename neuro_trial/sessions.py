from .evidence import at
from .enrollment import participants
def usage(db, known_at):
    people=participants(db,known_at);out=[]
    for row in at(db,'session',known_at):
        p=row['payload'];person=people.get(p['person'])
        if not person:out.append({'session':row['id'],'status':'受试者待核'});continue
        out.append({'person':p['person'],'stage':person['stage'],'minutes':p['minutes'],'completed':p['completed'],'source':row['digest'],'person_source':person['source']})
    return out
