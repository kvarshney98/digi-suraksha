import re
import httpx
from fastapi import HTTPException

# Only the PIN is sent to this fixed third-party directory; never send incident data.
async def lookup_pin(pin):
    if not re.fullmatch(r'[1-9][0-9]{5}', pin):
        raise HTTPException(422, 'Enter a six-digit PIN / छह अंकों का पिन लिखें')
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=False, trust_env=False) as client:
            async with client.stream('GET','https://api.postalpincode.in/pincode/'+pin) as response:
                response.raise_for_status()
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data)>1024*1024: raise ValueError('oversized directory response')
        import json
        payload=json.loads(data)
        offices=payload[0].get('PostOffice') or []
        locations=[]
        for office in offices[:200]:
            if str(office.get('Pincode'))!=pin or office.get('Country')!='India': continue
            item=dict(locality=str(office.get('Name') or '').strip()[:150],city=str(office.get('District') or '').strip()[:100],state=str(office.get('State') or '').strip()[:80],pincode=pin)
            if item not in locations: locations.append(item)
        return dict(locations=locations,provider='Postal PIN Code API (third-party)',source='https://api.postalpincode.in/',jurisdiction_verified=False)
    except Exception:
        raise HTTPException(503,'PIN lookup unavailable; enter state and city manually / पिन खोज उपलब्ध नहीं; राज्य और शहर स्वयं भरें')
