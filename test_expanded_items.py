from server import validate,WORK,PYTHON
from pypdf import PdfReader
import json,os,subprocess,copy
out=WORK/'prototype/test-output';base=json.loads((out/'case-0.json').read_text(encoding='utf-8'))
for count in [3,40,120]:
 d=copy.deepcopy(base);d['items']=[dict(name=f'พัสดุทดสอบลำดับ {i+1}',qty=1,price=1,vat=.07) for i in range(count)]
 d['budgets'][0]['itemIndices']=list(range(0,count,2));d['budgets'][1]['itemIndices']=list(range(1,count,2));validate(d)
 f=out/f'expanded-{count}.json';f.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');target=out/f'expanded-{count}.pdf';env=os.environ.copy();env.update(PSDP_DATA=str(f),PSDP_PDF=str(target))
 result=subprocess.run([PYTHON,str(WORK/'template-review/refine_pdf.py')],cwd=WORK,env=env,capture_output=True);assert result.returncode==0,result.stderr
 pdf=PdfReader(target);text=''.join(p.extract_text() for p in pdf.pages)
 assert 'รายละเอียดการจัดสรรงบประมาณ' not in text
 for i in range(count):assert text.count(f'พัสดุทดสอบลำดับ {i+1}\n')==2,(count,i)
 assert f'{count*1.07:,.2f}' in text
 print(f'PASS {count} items; {len(pdf.pages)} pages; every item twice; no budget appendix',flush=True)
