import sqlite3
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "incidents.sqlite3"
INDIA = timezone(timedelta(hours=5, minutes=30))

def connection():
    db = sqlite3.connect(DB)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, created TEXT, payload TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS attachments (id TEXT PRIMARY KEY, incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE, name TEXT, media_type TEXT, content BLOB)")
    db.execute("CREATE TABLE IF NOT EXISTS incident_counts (day TEXT PRIMARY KEY, count INTEGER NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS advisory_submissions (id TEXT PRIMARY KEY, created TEXT, status TEXT, payload TEXT, name TEXT, media_type TEXT, content BLOB)")
    # Seed historical counts once, before applying the existing retention policy.
    db.execute("CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY)")
    if not db.execute("SELECT 1 FROM migrations WHERE name='counts-v1'").fetchone():
        for (created,) in db.execute("SELECT created FROM incidents").fetchall():
            day = datetime.fromisoformat(created).astimezone(INDIA).date().isoformat()
            db.execute("INSERT INTO incident_counts VALUES (?,1) ON CONFLICT(day) DO UPDATE SET count=count+1", (day,))
        db.execute("INSERT INTO migrations VALUES ('counts-v1')")
    db.execute("DELETE FROM incidents WHERE created < ?", ((datetime.now(timezone.utc)-timedelta(days=30)).isoformat(),))
    db.commit()
    return db

def attachment_list(db, incident_id):
    return [dict(id=r[0], name=r[1], media_type=r[2], size=r[3]) for r in db.execute("SELECT id,name,media_type,length(content) FROM attachments WHERE incident_id=?", (incident_id,))]

def statistics():
    with connection() as db:
        day = datetime.now(INDIA).date().isoformat()
        row = db.execute("SELECT count FROM incident_counts WHERE day=?", (day,)).fetchone()
        total = db.execute("SELECT COALESCE(SUM(count),0) FROM incident_counts").fetchone()[0]
    return dict(today=row[0] if row else 0, total=total, timezone="Asia/Kolkata", date=day)

def draft(i, uploads=None):
    uploads = uploads or []
    hi = i.language == 'hi'
    def text(en, hin): return hin if hi else en
    record_id = i.record_id or str(uuid.uuid4())
    existing_files = []
    if i.record_id:
        with connection() as db:
            existing_files = attachment_list(db, record_id)
    if len(existing_files) + len(uploads) > 3 or sum(f['size'] for f in existing_files) + sum(len(f['content']) for f in uploads) > 5*1024*1024:
        raise ValueError('Maximum 3 attachments and 5 MB total / अधिकतम 3 फ़ाइल और कुल 5 MB')
    files = existing_files + [dict(id=str(uuid.uuid4()),name=f['name'],media_type=f['media_type'],size=len(f['content'])) for f in uploads]
    values = [
        (text('Incident','घटना'), i.description),
        (text('Outcome','स्थिति'), {'attempt':'संदिग्ध प्रयास','money':'धन की हानि','credentials':'जानकारी साझा की'}[i.outcome] if hi else i.outcome),
        (text('Date','दिनांक'), text('Unknown','अज्ञात') if i.date_unknown else i.date),
        (text('Time (IST)','समय (IST)'), text('Unknown','अज्ञात') if i.time_unknown else i.time + (text(' (approximate)',' (अनुमानित)') if i.time_approximate else '')),
        (text('Incident location (reported by user)','घटना का स्थान (उपयोगकर्ता के अनुसार)'), ', '.join(v for v in [i.locality,i.city,i.state,i.pincode] if v)),
        (text('Sender phone','भेजने वाले का फोन'), i.sender_phone),
        (text('Sender email','भेजने वाले का ईमेल'), i.sender_email),
        (text('Amount','राशि'), i.amount),
        (text('Transaction reference','लेनदेन संदर्भ'), i.reference),
        (text('Available evidence','उपलब्ध सबूत'), i.evidence),
        (text('Attachments','संलग्न फ़ाइलें'), ', '.join(f['name'] for f in files)),
        (text('Acknowledgement','पावती संख्या'), i.acknowledgement),
    ]
    title = text('Complaint concerning a suspected cyber incident','संदिग्ध साइबर घटना की शिकायत')
    report = title + '\n\n' + '\n\n'.join(k+': '+v for k,v in values if v) + '\n\n' + text('Please investigate and take appropriate action. These details reflect my account of the incident.','कृपया घटना की जाँच और उचित कार्रवाई करें। विवरण मेरे ज्ञान के अनुसार हैं।')
    email = text('Subject: ','विषय: ') + title + '\n\n' + text('Dear Sir/Madam,','महोदय/महोदया,') + '\n\n' + report
    guide = text('Draft only; no complaint has been filed. ','यह केवल मसौदा है; शिकायत दर्ज नहीं हुई है। ')
    guide += text('Contact your bank immediately, call 1930 and preserve evidence.','तुरंत बैंक से संपर्क करें, 1930 पर कॉल करें और सबूत सुरक्षित रखें।') if i.outcome=='money' else text('Change exposed passwords from a trusted device and revoke active sessions.','विश्वसनीय उपकरण से पासवर्ड बदलें और सक्रिय सत्र बंद करें।') if i.outcome=='credentials' else text('Stop engaging and verify through official channels.','संपर्क रोकें और आधिकारिक माध्यम से जाँच करें।')
    result = dict(report=report,email=email,guidance=guide,id=None,attachments=files)
    if i.save:
        result['id'] = record_id
        with connection() as db:
            existing = db.execute('SELECT created FROM incidents WHERE id=?',(record_id,)).fetchone()
            created = existing[0] if existing else datetime.now(timezone.utc).isoformat()
            payload = {**i.model_dump(), **result, 'record_id':record_id}
            db.execute('INSERT INTO incidents VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(record_id,created,json.dumps(payload,ensure_ascii=False)))
            for metadata, upload in zip(files[len(existing_files):], uploads):
                db.execute('INSERT INTO attachments VALUES (?,?,?,?,?)',(metadata['id'],record_id,upload['name'],upload['media_type'],upload['content']))
            if not existing:
                day = datetime.now(INDIA).date().isoformat()
                db.execute('INSERT INTO incident_counts VALUES (?,1) ON CONFLICT(day) DO UPDATE SET count=count+1',(day,))
    return result
