from .evidence import at
def participants(db, known_at):
    return {r['id']:{**r['payload'],'source':r['digest']} for r in at(db,'participant',known_at)}
