import re, ipaddress
from urllib.parse import urlsplit, parse_qs
from email import policy
from email.parser import Parser
from email.utils import parseaddr
from app.services.ai import interpret

def tr(en, hi, lang): return hi if lang == "hi" else en
RULES = [
("credentials", r"(?:share|send|provide|enter|बताएं|भेजें|साझा).{0,45}(?:otp|password|pin|पासवर्ड|ओटीपी)|(?:otp|password|pin|ओटीपी).{0,30}(?:share|send|भेजें)", "Request for secrets", "गोपनीय जानकारी की मांग", "Secrets can authorise access or payments.", "गोपनीय जानकारी से खाते या भुगतान का दुरुपयोग हो सकता है।"),
("urgency", r"urgent|immediately|within \d+|today|अभी|तुरंत|आज ही", "Pressure to act", "जल्दबाज़ी का दबाव", "Pressure discourages independent verification.", "दबाव स्वतंत्र जाँच करने से रोकता है।"),
("suspension", r"account.{0,25}(?:block|suspend)|kyc|खाता.{0,20}बंद|केवाईसी", "Account / KYC pressure", "खाता / केवाईसी दबाव", "Verify requests through your bank's independently found channel.", "अपने बैंक के आधिकारिक माध्यम से जाँच करें।"),
("prize", r"lottery|won a prize|claim.{0,15}reward|refund.{0,20}fee|लॉटरी|इनाम", "Prize or advance-fee offer", "इनाम या अग्रिम शुल्क प्रस्ताव", "Unexpected rewards can be used to solicit payments.", "अनपेक्षित इनाम से पैसे माँगे जा सकते हैं।"),
("job", r"job.{0,30}(?:fee|deposit)|registration fee|नौकरी.{0,30}(?:शुल्क|जमा)", "Recruitment payment", "नौकरी के लिए भुगतान", "Payment demands before employment deserve verification.", "नौकरी से पहले भुगतान की मांग की जाँच करें।"),
("investment", r"guaranteed.{0,20}return|double your money|loan.{0,20}fee|पैसा दोगुना|गारंटीड", "Financial promise", "वित्तीय वादा", "Guaranteed returns or upfront loan fees can indicate fraud.", "गारंटीड मुनाफा या ऋण से पहले शुल्क धोखाधड़ी का संकेत हो सकता है।"),
("arrest", r"digital arrest|safe account|money laundering|डिजिटल अरेस्ट|सुरक्षित खाते", "Coercion / safe-account claim", "धमकी / सुरक्षित खाते का दावा", "Do not transfer funds under threats; independently contact authorities.", "धमकी पर पैसे न भेजें; अधिकारियों से स्वतंत्र रूप से संपर्क करें।"),
("impersonation", r"cbi|rbi|police|government|customer.{0,2}care|पुलिस|सरकार", "Claimed authority", "अधिकार का दावा", "A claimed identity is not verified identity.", "बताई गई पहचान सत्यापित पहचान नहीं है।")]

def analyze_sync(content, kind, lang):
    indicators=[]
    def add(code,evidence,en,hi,why_en,why_hi):
        if not any(x["id"]==code and x["evidence"]==evidence for x in indicators): indicators.append(dict(id=code,evidence=evidence[:300],title=tr(en,hi,lang),explanation=tr(why_en,why_hi,lang)))
    if kind=="auto": kind="url" if re.fullmatch(r"https?://\S+",content.strip()) else ("email" if re.search(r"^From:",content,re.M|re.I) else "text")
    metadata={}
    if kind=="email":
        message=Parser(policy=policy.default).parsestr(content)
        metadata={k:str(message.get(k,""))[:500] for k in ["From","Reply-To","Subject","Authentication-Results"]}
        sender=parseaddr(metadata["From"])[1].lower(); reply=parseaddr(metadata["Reply-To"])[1].lower()
        if sender and reply and sender.split('@')[-1]!=reply.split('@')[-1]: add("reply_mismatch",reply,"Reply-to domain differs","उत्तर का डोमेन अलग है","Replies go to a different domain.","उत्तर अलग डोमेन पर जाएगा।")
        auth=metadata["Authentication-Results"]
        if re.search(r"(?:spf|dkim|dmarc)=fail",auth,re.I): add("auth_fail",auth,"Email authentication failure","ईमेल प्रमाणीकरण विफल","Reported header results can indicate spoofing; pasted headers are unverified.","हेडर में विफलता जालसाजी का संकेत है; चिपकाए हेडर सत्यापित नहीं हैं।")
        parts=[]
        for p in message.walk():
            if p.get_content_type() in {"text/plain","text/html"}:
                try: parts.append(p.get_content())
                except Exception: pass
        content=metadata["Subject"]+'\n'+'\n'.join(parts)
    for code,pattern,en,hi,we,wh in RULES:
        match=re.search(pattern,content,re.I|re.S)
        if match and not (code == "credentials" and re.search(r"never\s+(?:share|send)|do not\s+(?:share|send)|न\s*(?:भेजें|साझा)", content, re.I)):
            add(code,match.group(),en,hi,we,wh)
    urls=re.findall(r"https?://[^\s<>\"']+",content)
    if kind=="url": urls=[content.strip()]
    for url in urls[:30]:
        try:
            parsed=urlsplit(url); host=(parsed.hostname or '').lower(); _=parsed.port
            if parsed.scheme not in {"http","https"} or not host: raise ValueError()
            checks=[]
            if parsed.scheme=="http": checks.append(("unencrypted","Unencrypted link","असुरक्षित कनेक्शन"))
            if parsed.username or parsed.password: checks.append(("embedded_credentials","Embedded credentials","लिंक में लॉगिन जानकारी"))
            try:
                ip=ipaddress.ip_address(host)
                checks.append(("ip_host","IP-address destination","आईपी पते वाला लिंक"))
                if not ip.is_global: checks.append(("private_host","Internal network destination","आंतरिक नेटवर्क पता"))
            except ValueError:
                if host=="localhost" or host.endswith((".local",".localhost",".internal")): checks.append(("private_host","Internal hostname","आंतरिक होस्ट नाम"))
            if host in {"bit.ly","tinyurl.com","t.co","shorturl.at"}: checks.append(("shortener","Shortened link","छोटा किया गया लिंक"))
            if 'xn--' in host or any(ord(c)>127 for c in host): checks.append(("lookalike","Internationalised hostname","अंतरराष्ट्रीय अक्षरों वाला डोमेन"))
            if host.count('.')>=3 or re.search(r"(?:sbi|hdfc|icici|gov|bank).*(?:verify|kyc|secure|login)|(?:verify|kyc|secure).*(?:sbi|bank)",host): checks.append(("misleading_domain","Potentially misleading hostname","भ्रामक होस्ट नाम का संकेत"))
            if set(parse_qs(parsed.query)) & {"password","otp","pin","redirect","redirect_uri","token"}: checks.append(("query","Sensitive / redirect query parameter","संवेदनशील / रीडायरेक्ट पैरामीटर"))
            for code,en,hi in checks: add(code,url,en,hi,"The URL structure warrants independent verification. No destination was visited.","लिंक की संरचना की स्वतंत्र जाँच करें। लिंक खोला नहीं गया।")
        except ValueError: add("invalid_url",url,"Malformed URL","अमान्य लिंक","The destination cannot be reliably parsed.","गंतव्य का भरोसेमंद विश्लेषण नहीं हो सका।")
    ids={x['id'] for x in indicators}
    risk='Critical' if 'arrest' in ids and ('credentials' in ids or 'urgency' in ids) else 'High' if 'credentials' in ids or 'arrest' in ids or len(ids)>=3 else 'Moderate' if ids else 'Low'
    return kind,indicators,metadata,risk,content

async def analyze(content,kind,lang,consent=False):
    kind,findings,metadata,risk,extracted=analyze_sync(content,kind,lang)
    ai,provider=await interpret(findings,lang,consent)
    return dict(input_type=kind,risk=risk,assessment=tr("Provisional rule-based assessment; low risk does not mean safe.","नियम आधारित प्रारंभिक आकलन; कम जोखिम का अर्थ सुरक्षित नहीं है।",lang),indicators=findings,metadata=metadata,confidence=tr("Limited: sender identity, destination reputation and factual claims are not verified.","सीमित: भेजने वाले की पहचान, लिंक की प्रतिष्ठा और दावे सत्यापित नहीं हैं।",lang),potential_impact=tr("Possible account access or financial loss if you act on an unverified request.","असत्यापित अनुरोध पर कार्रवाई से खाते या धन को नुकसान संभव है।",lang),actions=[tr("Do not share OTPs, PINs or passwords. Verify independently using official contact details.","ओटीपी, पिन या पासवर्ड साझा न करें। आधिकारिक संपर्क से स्वतंत्र जाँच करें।",lang),tr("If money was lost, contact your bank immediately and call 1930; preserve evidence and report at cybercrime.gov.in.","पैसे खोने पर तुरंत बैंक से संपर्क करें और 1930 पर कॉल करें; सबूत सुरक्षित रखकर cybercrime.gov.in पर रिपोर्ट करें।",lang)],reporting_route="ncrp" if risk in {'High','Critical'} else "suspect",ai=ai,provider=provider,extracted_text=extracted[:30000])
