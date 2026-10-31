import json
from pathlib import Path
from app.services.detection import analyze_sync
cases=[
('Send OTP immediately to stop account suspension',True,'en'),
('You are under digital arrest. Transfer to our safe account now',True,'en'),
('Job offer: pay registration fee',True,'en'),
('Guaranteed return: double your money',True,'en'),
('आपका खाता आज ही बंद होगा। ओटीपी भेजें',True,'hi'),
('नौकरी के लिए शुल्क जमा करें',True,'hi'),
('OTP दर्ज करें और अपना खाता सत्यापित करें',True,'hi'),
('Your parcel delivery requires a small payment',True,'en'),
('Library opens tomorrow',False,'en'),
('Never share your OTP',False,'en'),
('Your appointment is today at 10',False,'en'),
('Urgent: team meeting moved to noon',False,'en'),
('नमस्ते, पुस्तकालय कल खुलेगा',False,'hi'),
('आज ही अपना गृहकार्य पूरा करें',False,'hi'),
('https://example.com/about',False,'en'),
('Dinner at six?',False,'en')]
counts=dict(tp=0,tn=0,fp=0,fn=0);results=[]
for text,positive,lang in cases:
    kind,findings,metadata,risk,_=analyze_sync(text,'auto',lang)
    predicted=risk!='Low'
    key=('tp' if predicted else 'fn') if positive else ('fp' if predicted else 'tn')
    counts[key]+=1
    results.append(dict(content=text,label='suspicious' if positive else 'benign',language=lang,risk=risk,outcome=key))
report={'note':'16 synthetic manually labelled development examples, not a representative accuracy benchmark. Positive means any configured warning (Moderate or above).','counts':counts,'precision':round(counts['tp']/(counts['tp']+counts['fp']),3),'recall':round(counts['tp']/(counts['tp']+counts['fn']),3),'cases':results}
Path('data/quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
