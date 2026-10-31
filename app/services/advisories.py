import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlsplit
from app.services.incidents import connection

class AdvisorySubmission(BaseModel):
    language: Literal['en','hi'] = 'en'
    title: str = Field(min_length=3,max_length=150)
    looks: str = Field(min_length=10,max_length=3000)
    signs: str = Field(default='',max_length=2000)
    action: str = Field(default='',max_length=2000)
    avoid: str = Field(default='',max_length=2000)
    after: str = Field(default='',max_length=2000)
    source: str = Field(min_length=8,max_length=1000)

    @field_validator('title','looks')
    @classmethod
    def nonblank(cls,value):
        if not value.strip(): raise ValueError('Content required / सामग्री आवश्यक है')
        return value.strip()

    @field_validator('source')
    @classmethod
    def source_url(cls,value):
        parsed=urlsplit(value)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Use an HTTPS source URL / HTTPS स्रोत लिंक लिखें')
        return value

def public_advisories():
    rows=json.loads((Path(__file__).resolve().parents[2]/'data/advisories.json').read_text(encoding='utf-8'))
    with connection() as db:
        additions=db.execute("SELECT id,payload,name FROM advisory_submissions WHERE status='published' ORDER BY created DESC").fetchall()
    for identifier,payload,name in additions:
        item=json.loads(payload)
        rows.append(dict(id=identifier,**{k:{'en':item[k] if item['language']=='en' else '', 'hi':item[k] if item['language']=='hi' else ''} for k in ['title','looks','signs','action','avoid','after']},resource='ncrp',source=item['source'],uploaded=True,language=item['language'],attachment_name=name,attachment_url='/api/advisories/'+identifier+'/attachment' if name else None))
    return rows

def submit_advisory(item,upload=None):
    identifier=str(uuid.uuid4())
    with connection() as db:
        db.execute('INSERT INTO advisory_submissions VALUES (?,?,?,?,?,?,?)',(identifier,datetime.now(timezone.utc).isoformat(),'pending',item.model_dump_json(),upload['name'] if upload else None,upload['media_type'] if upload else None,upload['content'] if upload else None))
    return dict(id=identifier,status='pending')
