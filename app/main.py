import io, json, os, shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
import pytesseract
from starlette.concurrency import run_in_threadpool
from app.schemas import AnalysisRequest, Incident
from app.services.detection import analyze, tr
from app.services.incidents import draft, connection
from app.services.advisories import public_advisories
from app.resources_api import router as resources_router
BASE=Path(__file__).resolve().parent
app=FastAPI(title="DIGI SURAKSHA",version="1.0.0")
Image.MAX_IMAGE_PIXELS=12000000

@app.middleware('http')
async def guards(request: Request, call_next):
    if request.headers.get('host','').split(':')[0] not in {'127.0.0.1','localhost','testserver'}: return JSONResponse({'detail':'Invalid host'},400)
    if request.method not in {'GET','HEAD','OPTIONS'}:
        origin=request.headers.get('origin')
        if origin and origin not in {'http://127.0.0.1:8000','http://localhost:8000'}: return JSONResponse({'detail':'Invalid origin'},403)
    try:
        length=int(request.headers.get('content-length','0'))
    except ValueError: return JSONResponse({'detail':'Invalid length'},400)
    if length>6*1024*1024: return JSONResponse({'detail':'Request exceeds 6 MB'},413)
    if request.method in {'POST', 'PUT', 'PATCH'}:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 6*1024*1024:
                return JSONResponse({'detail':'Request exceeds 6 MB'},413)
        request._body = bytes(body)
    response=await call_next(request)
    response.headers.update({'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"})
    if request.url.path in {'/docs', '/redoc'}:
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'; frame-ancestors 'none'"
    return response

@app.exception_handler(Exception)
async def unexpected(request,exc): return JSONResponse({'detail':'Unable to complete request / अनुरोध पूरा नहीं हुआ'},500)

@app.get('/api/health')
def health():
    return {'status':'ok','ocr':bool(shutil.which('tesseract')),'remote_configured':bool(os.getenv('REMOTE_AI_URL')),'local_configured':bool(os.getenv('LOCAL_AI_URL'))}
@app.post('/api/analyze')
async def analyze_input(body: AnalysisRequest):
    if not body.content.strip(): raise HTTPException(422,'Enter content / सामग्री लिखें')
    return await analyze(body.content,body.input_type,body.language,body.remote_consent)

@app.post('/api/analyze/upload')
async def upload(file: UploadFile=File(...),language: str=Form('en'),remote_consent: bool=Form(False)):
    if language not in {'en','hi'}: raise HTTPException(422,'Invalid language / अमान्य भाषा')
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise HTTPException(413,tr('Maximum file size is 5 MB','अधिकतम फ़ाइल आकार 5 MB है',language))
    ext=Path(file.filename or '').suffix.lower()
    if ext=='.eml':
        content=data.decode('utf-8',errors='replace')
        if len(content)>30000: raise HTTPException(422,tr('Email exceeds 30,000 characters','ईमेल 30,000 अक्षरों से अधिक है',language))
        return await analyze(content,'email',language,remote_consent)
    if ext not in {'.png','.jpg','.jpeg','.webp'}: raise HTTPException(415,tr('Use PNG, JPG, WEBP or EML','PNG, JPG, WEBP या EML चुनें',language))
    try:
        image=Image.open(io.BytesIO(data))
        if image.format not in {'PNG','JPEG','WEBP'} or image.width*image.height>12000000: raise ValueError()
        image.load()
    except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError): raise HTTPException(422,tr('Unreadable or oversized image','चित्र पढ़ने योग्य नहीं या बहुत बड़ा है',language))
    try:
        langs=pytesseract.get_languages(config='')
        content=await run_in_threadpool(pytesseract.image_to_string,image,lang='eng+hin' if 'hin' in langs else 'eng',timeout=15)
    except Exception: raise HTTPException(503,tr('OCR unavailable. Install Tesseract or paste the text.','OCR उपलब्ध नहीं। Tesseract स्थापित करें या पाठ चिपकाएँ।',language))
    if not content.strip(): raise HTTPException(422,tr('No readable text found; paste the text instead.','पढ़ने योग्य पाठ नहीं मिला; पाठ चिपकाएँ।',language))
    result=await analyze(content[:30000],'text',language,remote_consent)
    result['input_type']='screenshot'
    if 'hin' not in langs:
        result['confidence']+=' '+tr('Hindi OCR language data is not installed; Hindi screenshots may be unreadable.','हिन्दी OCR भाषा डेटा स्थापित नहीं है; हिन्दी स्क्रीनशॉट पढ़ना संभव नहीं हो सकता।',language)
    result['confidence']+=' '+tr('OCR can misread characters; check the extracted text.','OCR अक्षर गलत पढ़ सकता है; निकाले पाठ की जाँच करें।',language)
    return result

@app.get('/api/reporting')
def reporting(): return json.loads((BASE.parent/'data/reporting_directory.json').read_text(encoding='utf-8'))
@app.get('/api/advisories')
def advisories(): return public_advisories()
@app.post('/api/incidents')
def incident(body: Incident): return draft(body)
@app.get('/api/incidents')
def history():
    with connection() as db: return [{'id':r[0],'created':r[1],**json.loads(r[2])} for r in db.execute('SELECT * FROM incidents ORDER BY created DESC')]
@app.delete('/api/incidents/{incident_id}')
def delete(incident_id: str):
    with connection() as db: db.execute('DELETE FROM incidents WHERE id=?',(incident_id,))
    return {'deleted':True}
app.include_router(resources_router)
app.mount('/static',StaticFiles(directory=BASE/'web'),name='static')
@app.get('/')
@app.get('/detect')
@app.get('/response')
@app.get('/awareness')
@app.get('/reporting')
@app.get('/privacy')
def page(): return FileResponse(BASE/'web/index.html')
