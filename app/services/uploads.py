import io
import re
from pathlib import PurePath
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

MAX_TOTAL = 5*1024*1024

async def read_upload(file):
    content = await file.read(MAX_TOTAL+1)
    if not content or len(content)>MAX_TOTAL:
        raise HTTPException(413, 'Use non-empty files up to 5 MB / खाली फ़ाइल न चुनें; अधिकतम 5 MB')
    # Never use a supplied filename as a filesystem path.
    name = re.sub(r'[\x00-\x1f\x7f]', '', (file.filename or 'attachment').replace('\\','/').rsplit('/',1)[-1])[:180]
    extension = PurePath(name).suffix.lower()
    media = {'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.pdf':'application/pdf','.txt':'text/plain','.eml':'message/rfc822'}.get(extension)
    if not media:
        raise HTTPException(415, 'Use PNG, JPG, WEBP, PDF, TXT or EML / PNG, JPG, WEBP, PDF, TXT या EML चुनें')
    try:
        if media.startswith('image/'):
            image = Image.open(io.BytesIO(content))
            if image.format not in {'PNG','JPEG','WEBP'} or image.width*image.height>12000000:
                raise ValueError()
            expected = {'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}[image.format]
            if expected != media: raise ValueError()
            image.verify()
        elif extension == '.pdf':
            if not content.startswith(b'%PDF-') or b'%%EOF' not in content[-2048:]: raise ValueError()
        else:
            decoded = content.decode('utf-8-sig')
            if '\x00' in decoded: raise ValueError()
    except (ValueError, UnicodeDecodeError, UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(422, 'Unreadable file or contents do not match its type / फ़ाइल अमान्य है या प्रकार से मेल नहीं खाती')
    return dict(name=name,media_type=media,content=content)

async def read_attachments(files):
    if len(files)>3: raise HTTPException(422,'Maximum 3 attachments / अधिकतम 3 फ़ाइलें')
    uploads = [await read_upload(file) for file in files]
    if sum(len(f['content']) for f in uploads)>MAX_TOTAL:
        raise HTTPException(413,'Attachments must total at most 5 MB / कुल फ़ाइल आकार अधिकतम 5 MB')
    return uploads
