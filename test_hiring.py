from server import validate,WORK,PYTHON
from pypdf import PdfReader
import json,os,subprocess
out=WORK/'prototype/test-output';d=json.loads((out/'layout.json').read_text(encoding='utf-8'));d['supervisor']=d['officer']
for mode in ['purchase','hiring']:
 d['documentType']=mode;validate(d);f=out/(mode+'-mode.json');f.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');pdf=out/(mode+'-mode.pdf');env=os.environ.copy();env.update(PSDP_DATA=str(f),PSDP_PDF=str(pdf));subprocess.run([PYTHON,str(WORK/'template-review/refine_pdf.py')],cwd=WORK,env=env,check=True,capture_output=True)
 text=''.join(p.extract_text() for p in PdfReader(pdf).pages)
 assert ('8. ขออนุมัติแต่งตั้งผู้ควบคุมงาน' in text)==(mode=='hiring')
 assert ('รายงานขอจ้าง' if mode=='hiring' else 'รายงานขอซื้อ') in text
 assert ('รายงานผลการพิจารณาและขออนุมัติสั่งจ้าง' if mode=='hiring' else 'รายงานผลการพิจารณาและขออนุมัติสั่งซื้อ') in text
 print('PASS',mode,flush=True)
