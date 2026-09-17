from pathlib import Path
import json,os,subprocess
from server import WORK,PYTHON,validate
from pypdf import PdfReader
out=WORK/'prototype/test-output';d=json.loads((out/'case-2.json').read_text(encoding='utf-8'));m=json.loads((WORK/'prototype/master-data.json').read_text(encoding='utf-8'))
for k,person in zip(['chair','member1','member2','officer','approver','receiver'],m['people']):d[k]=person['name']
validate(d);f=out/'layout.json';f.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');pdf=out/'layout.pdf';env=os.environ.copy();env.update(PSDP_DATA=str(f),PSDP_PDF=str(pdf));subprocess.run([PYTHON,str(WORK/'template-review/refine_pdf.py')],cwd=WORK,env=env,check=True,capture_output=True)
reader=PdfReader(pdf);text=''.join(p.extract_text() for p in reader.pages)
assert 'เอกสารจัดซื้อ (ต่อ)' not in text
for person in m['people'][:3]:assert person['position'] in text
print('PASS positions and no continuation heading;',len(reader.pages),'pages')
