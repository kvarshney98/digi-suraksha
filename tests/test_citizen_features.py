import io
import json
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services import incidents
from app.services.locations import lookup_pin

client = TestClient(app)

@pytest.fixture(autouse=True)
def local_database(tmp_path, monkeypatch):
    monkeypatch.setattr(incidents, 'DB', tmp_path / 'features.sqlite3')


def incident(**changes):
    return {'description': 'Synthetic test incident only', 'date': '2026-10-30', 'time': '14:30', **changes}


def prepare(payload, files=None):
    return client.post('/api/incidents/prepare', data={'payload': json.dumps(payload)}, files=files or [])

@pytest.mark.parametrize('changes', [
    {'date': ''}, {'time': ''}, {'date_unknown': True}, {'time_unknown': True},
    {'date': '2026-02-30'}, {'time': '29:00'}, {'time': '9:00'},
    {'pincode': '../../'}, {'pincode': '000000'}, {'sender_email': 'invalid'},
    {'sender_phone': '+x'}, {'record_id': '../../file'},
    {'time': '', 'time_unknown': True, 'time_approximate': True},
])
def test_required_date_time_and_validation(changes):
    assert prepare(incident(**changes)).status_code == 422


def test_explicit_unknown_and_optional_time_approximation():
    result = prepare(incident(date='',time='',date_unknown=True,time_unknown=True,language='hi')).json()
    assert 'अज्ञात' in result['report']
    assert 'ड्राफ्ट' not in result['report']  # not an invented submitted status
    result = prepare(incident(time_approximate=True)).json()
    assert '14:30 (approximate)' in result['report']


def test_location_sender_in_drafts():
    response = prepare(incident(pincode='452001',state='Madhya Pradesh',city='Indore',locality='Indore',sender_phone='+442012345678',sender_email='synthetic@example.org'))
    assert response.status_code == 200
    text = response.json()['report']
    assert all(value in text for value in ['452001','Indore','+442012345678','synthetic@example.org'])
    assert 'fraudulent international number' not in text


def test_saved_attachments_download_delete_and_unique_counter():
    key = str(uuid.uuid4())
    payload = incident(save=True,record_id=key)
    response = prepare(payload,[('files',('../evidence.txt',b'Synthetic evidence only','text/plain'))])
    assert response.status_code == 200, response.text
    record = response.json()
    file = record['attachments'][0]
    assert file['name']=='evidence.txt'
    assert 'evidence.txt' in record['report']
    download=client.get(f"/api/incidents/{key}/attachments/{file['id']}")
    assert download.content==b'Synthetic evidence only'
    assert download.headers['content-disposition'].startswith('attachment;')
    assert client.get('/api/stats').json()['total']==1
    assert prepare(payload).status_code==200
    assert client.get('/api/stats').json()['total']==1
    assert len(client.get('/api/incidents').json()[0]['attachments'])==1
    client.delete('/api/incidents/'+key)
    assert client.get(f"/api/incidents/{key}/attachments/{file['id']}").status_code==404
    assert client.get('/api/stats').json()['total']==1  # cumulative, anonymous counts


def test_unsaved_files_not_retained_or_counted():
    response=prepare(incident(),[('files',('evidence.txt',b'Synthetic evidence','text/plain'))])
    assert response.status_code==200 and response.json()['id'] is None
    assert response.json()['attachments'][0]['name']=='evidence.txt'
    with incidents.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM attachments').fetchone()[0]==0
    assert client.get('/api/stats').json()['total']==0

@pytest.mark.parametrize('files,status', [
    ([('files',('payload.exe',b'MZ','application/octet-stream'))],415),
    ([('files',('fake.png',b'not png','image/png'))],422),
    ([('files',('fake.pdf',b'not pdf','application/pdf'))],422),
    ([('files',('binary.txt',b'abc\x00def','text/plain'))],422),
    ([('files',(f'{n}.txt',b'fixture','text/plain')) for n in range(4)],422),
    ([('files',('large.txt',b'x'*(5*1024*1024+1),'text/plain'))],413),
])
def test_evidence_rejection(files,status):
    assert prepare(incident(),files).status_code==status


def test_real_image_attachment_and_deletion():
    image=Image.new('RGB',(10,10),'white');stream=io.BytesIO();image.save(stream,format='PNG')
    result=prepare(incident(save=True),[('files',('evidence.png',stream.getvalue(),'image/png'))]).json()
    file=result['attachments'][0]
    path=f"/api/incidents/{result['id']}/attachments/{file['id']}"
    assert client.get(path).content==stream.getvalue()
    assert client.delete(path).status_code==200
    assert client.get(path).status_code==404


def test_retention_cascades_attachments():
    result=prepare(incident(save=True),[('files',('evidence.txt',b'Synthetic evidence','text/plain'))]).json()
    with incidents.connection() as db:
        db.execute('UPDATE incidents SET created=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(days=31)).isoformat(),result['id']))
    assert client.get('/api/incidents').json()==[]
    with incidents.connection() as db: assert db.execute('SELECT COUNT(*) FROM attachments').fetchone()[0]==0


def test_stats_ist_and_new_incidents():
    today=datetime.now(incidents.INDIA).date().isoformat()
    assert client.get('/api/stats').json()['date']==today
    prepare(incident(save=True));prepare(incident(save=True))
    result=client.get('/api/stats').json()
    assert result['today']==2 and result['total']==2


def advisory_payload(**extra):
    return {'language':'en','title':'Synthetic advisory','looks':'Synthetic awareness content for tests only.','source':'https://example.org/advisory',**extra}


def test_advisory_review_publish_search_and_delete():
    initial=len(client.get('/api/advisories').json())
    response=client.post('/api/advisories/upload',data={'payload':json.dumps(advisory_payload())},files={'file':('advisory.txt',b'Synthetic advisory','text/plain')})
    assert response.status_code==200,response.text
    key=response.json()['id']
    assert response.json()['status']=='pending'
    assert len(client.get('/api/advisories').json())==initial
    assert client.get('/api/advisories/review').json()[0]['title']=='Synthetic advisory'
    assert client.post(f'/api/advisories/{key}/publish',json={'reviewed':False}).status_code==422
    assert client.post(f'/api/advisories/{key}/publish',json={'reviewed':True}).status_code==200
    published=client.get('/api/advisories').json()[-1]
    assert published['uploaded'] and published['title']['en']=='Synthetic advisory'
    assert client.get(published['attachment_url']).content==b'Synthetic advisory'
    assert client.delete('/api/advisories/'+key).status_code==200
    assert len(client.get('/api/advisories').json())==initial
    assert client.get(published['attachment_url']).status_code==404

@pytest.mark.parametrize('source',['javascript:alert(1)','http://example.org','https://user:pass@example.org'])
def test_advisory_source_validation(source):
    assert client.post('/api/advisories/upload',data={'payload':json.dumps(advisory_payload(source=source))}).status_code==422


def test_banks_and_videos():
    banks=client.get('/api/banks').json()
    assert len(banks)==5 and any(b['id']=='hsbc' for b in banks)
    assert all(b['source'].startswith('https://') and b['last_verified']=='2026-10-31' for b in banks)
    items=client.get('/api/advisories').json()
    assert len(items)==10
    assert all(item['video_channel']['url'].startswith('https://www.youtube.com/') for item in items)
    assert sum(len(item['videos']) for item in items)==2


def test_pin_lookup_fixed_origin_and_response(monkeypatch):
    response=[{'PostOffice':[{'Name':'Synthetic locality','District':'Indore','State':'Madhya Pradesh','Country':'India','Pincode':'452001'}]}]
    urls=[]
    def handler(request):
        urls.append(str(request.url))
        return httpx.Response(200,json=response)
    real=httpx.AsyncClient
    monkeypatch.setattr('app.services.locations.httpx.AsyncClient',lambda **kwargs:real(transport=httpx.MockTransport(handler),**kwargs))
    result=client.get('/api/locations/452001')
    assert result.status_code==200,result.text
    assert result.json()['locations'][0]['city']=='Indore'
    assert result.json()['jurisdiction_verified'] is False
    assert urls==['https://api.postalpincode.in/pincode/452001']
    assert client.get('/api/locations/123').status_code==422


def test_pin_failure_allows_manual_entry(monkeypatch):
    def handler(request): raise httpx.ConnectError('offline')
    real=httpx.AsyncClient
    monkeypatch.setattr('app.services.locations.httpx.AsyncClient',lambda **kwargs:real(transport=httpx.MockTransport(handler),**kwargs))
    response=client.get('/api/locations/452001')
    assert response.status_code==503 and 'manually' in response.json()['detail']
    assert prepare(incident(state='Madhya Pradesh',city='Indore')).status_code==200
