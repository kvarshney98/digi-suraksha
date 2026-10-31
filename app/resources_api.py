import json
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError
from app.schemas import Incident
from app.services.incidents import draft, connection, statistics
from app.services.uploads import read_upload, read_attachments
from app.services.locations import lookup_pin
from app.services.advisories import AdvisorySubmission, submit_advisory

router=APIRouter(prefix='/api')
DATA=Path(__file__).resolve().parent.parent/'data'

def download(content, name, media_type):
    return Response(content,media_type=media_type,headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(name,safe=''),'X-Content-Type-Options':'nosniff'})

@router.get('/banks')
def banks(): return json.loads((DATA/'banks.json').read_text(encoding='utf-8'))

@router.get('/locations/states')
def states(): return json.loads((DATA/'states.json').read_text(encoding='utf-8'))

@router.get('/locations/{pin}')
async def locations(pin: str): return await lookup_pin(pin)

@router.get('/stats')
def stats(): return statistics()

@router.post('/incidents/prepare')
async def prepare(payload: str=Form(...),files: list[UploadFile]=File(default=[])):
    try: incident=Incident.model_validate_json(payload)
    except ValidationError: raise HTTPException(422,'Check required date/time choices and incident fields / दिनांक, समय और घटना की जानकारी जाँचें')
    uploads=await read_attachments(files)
    try: return draft(incident,uploads)
    except ValueError as exc: raise HTTPException(422,str(exc))

@router.get('/incidents/{incident_id}/attachments/{attachment_id}')
def incident_attachment(incident_id: str,attachment_id: str):
    with connection() as db:
        row=db.execute('SELECT content,name,media_type FROM attachments WHERE incident_id=? AND id=?',(incident_id,attachment_id)).fetchone()
    if not row: raise HTTPException(404,'Attachment not found / फ़ाइल नहीं मिली')
    return download(*row)

@router.delete('/incidents/{incident_id}/attachments/{attachment_id}')
def delete_attachment(incident_id: str,attachment_id: str):
    with connection() as db:
        db.execute('DELETE FROM attachments WHERE incident_id=? AND id=?',(incident_id,attachment_id))
        row=db.execute('SELECT payload FROM incidents WHERE id=?',(incident_id,)).fetchone()
        if row:
            item=json.loads(row[0]);item['attachments']=[f for f in item.get('attachments',[]) if f['id']!=attachment_id]
            db.execute('UPDATE incidents SET payload=? WHERE id=?',(json.dumps(item,ensure_ascii=False),incident_id))
    return dict(deleted=True)

@router.post('/advisories/upload')
async def upload_advisory(payload: str=Form(...),file: UploadFile | None=File(None)):
    try: item=AdvisorySubmission.model_validate_json(payload)
    except ValidationError: raise HTTPException(422,'Add a title, description and HTTPS source / शीर्षक, विवरण और HTTPS स्रोत लिखें')
    upload=await read_upload(file) if file and file.filename else None
    if upload and upload['media_type'] not in {'application/pdf','text/plain','image/png','image/jpeg','image/webp'}:
        raise HTTPException(415,'Use PDF, TXT or an image for advisories / जानकारी के लिए PDF, TXT या चित्र चुनें')
    return submit_advisory(item,upload)

@router.get('/advisories/review')
def review_queue():
    with connection() as db:
        return [dict(id=r[0],created=r[1],status=r[2],**json.loads(r[3]),attachment_name=r[4]) for r in db.execute('SELECT id,created,status,payload,name FROM advisory_submissions ORDER BY created DESC')]

class ReviewDecision(BaseModel):
    reviewed: bool = False

@router.post('/advisories/{identifier}/publish')
def publish(identifier: str,decision: ReviewDecision):
    if not decision.reviewed: raise HTTPException(422,'Review the content and source before publishing / प्रकाशन से पहले सामग्री और स्रोत की समीक्षा करें')
    with connection() as db:
        cursor=db.execute("UPDATE advisory_submissions SET status='published' WHERE id=?",(identifier,))
        if not cursor.rowcount: raise HTTPException(404,'Not found / नहीं मिला')
    return dict(status='published')

@router.delete('/advisories/{identifier}')
def remove_advisory(identifier: str):
    with connection() as db: db.execute('DELETE FROM advisory_submissions WHERE id=?',(identifier,))
    return dict(deleted=True)

@router.get('/advisories/{identifier}/attachment')
def advisory_attachment(identifier: str):
    with connection() as db: row=db.execute('SELECT content,name,media_type FROM advisory_submissions WHERE id=? AND content IS NOT NULL',(identifier,)).fetchone()
    if not row: raise HTTPException(404,'Not found / नहीं मिला')
    return download(*row)
