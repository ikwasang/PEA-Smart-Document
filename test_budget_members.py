from server import validate,WORK,PYTHON
from pathlib import Path
import copy,json,os,subprocess
from pypdf import PdfReader
d=dict(department='ผปร.',description='ทดสอบแยกงบสินค้า',reason='เพื่อทดแทนวัสดุเดิม',vendor='ผู้ขายตัวอย่าง',days=3,chair='ประธานทดสอบ',officer='เจ้าหน้าที่ทดสอบ',approver='ผู้อนุมัติทดสอบ',receiver='ผู้รับทดสอบ',items=[dict(name='สินค้า ก',qty=1,price=100,vat=7),dict(name='สินค้า ข',qty=1,price=200,vat=14)],budgets=[dict(type='งบทำการ',costCenter='A311201010',expense='วัสดุ',account='บัญชี A',itemIndices=[0]),dict(type='งบแฟ้มงาน',costCenter='A311201020',budgetFile='แฟ้มทดสอบ',network='โครงข่ายทดสอบ',expense='วัสดุ',account='บัญชี B',itemIndices=[1])])
out=WORK/'prototype/test-output';out.mkdir(exist_ok=True)
for n in range(3):
 x=copy.deepcopy(d)
 for i in range(n):x['member'+str(i+1)]='กรรมการทดสอบ'+str(i+1)
 assert validate(x)==(30000,2100)
 f=out/f'case-{n}.json';f.write_text(json.dumps(x,ensure_ascii=False),encoding='utf-8');env=os.environ.copy();env['PSDP_DATA']=str(f);env['PSDP_PDF']=str(out/f'case-{n}.pdf')
 p=subprocess.run([PYTHON,str(WORK/'template-review/refine_pdf.py')],cwd=WORK,env=env,capture_output=True)
 assert p.returncode==0,p.stderr
 pdf=PdfReader(out/f'case-{n}.pdf');assert len(pdf.pages)>=5
 text=''.join(p.extract_text() for p in pdf.pages)
 for k in ['A311201010','A311201020','321.00']:assert k in text,k
 for i in range(2):assert (('กรรมการทดสอบ'+str(i+1)) in text)==(i<n)
for mutation in ['duplicate','missing','same-person']:
 x=copy.deepcopy(d)
 if mutation=='duplicate':x['budgets'][1]['itemIndices']=[0,1]
 if mutation=='missing':x['budgets'][1]['itemIndices']=[]
 if mutation=='same-person':x['member1']=x['chair']
 try:validate(x);raise AssertionError(mutation)
 except ValueError:pass
print('PASS: 0/1/2 members; 2 budgets; PDF amounts and selected members; duplicates and missing allocations rejected')
