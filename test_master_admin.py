from pathlib import Path
from tempfile import TemporaryDirectory
import json
from master_admin import parse_excel,preview,commit
ROOT=Path(__file__).resolve().parent
source=Path('D:/SuperAng project/ไฟล์ต้นแบบสำหรับ export')
files={'budgets':'Data ของงบแฟ้มงาน.xlsx','accounts':'รหัสบัญชี.xlsx','people':'รายชื่อ ประธานกรรมการ, กรรมการ และเจ้าหน้าที่จัดทำเอกสาร.xlsx'}
original=(ROOT/'master-data.json').read_bytes()
with TemporaryDirectory(dir=ROOT/'tmp') as location:
 root=Path(location);(root/'master-data.json').write_bytes(original)
 for kind,name in files.items():
  old=(root/'master-data.json').read_bytes();result=preview(root,kind,(source/name).read_bytes(),name)
  assert (root/'master-data.json').read_bytes()==old,'Preview changed data'
  before=json.loads(old);saved=commit(root,result['token']);after=json.loads((root/'master-data.json').read_bytes())
  for key in ['budgetFiles','accounts','costCenters','people']:
   if key not in {'budgets':['budgetFiles'],'accounts':['accounts','costCenters'],'people':['people']}[kind]:assert before[key]==after[key]
  assert (root/'local-data'/'master-backups'/saved['backup']).read_bytes()==old
  assert saved['counts']=={'budgetFiles':20,'networks':66,'accounts':177,'costCenters':4,'people':16}
  print('PASS preview, commit, backup, preserve other groups:',kind,flush=True)
 for kind,raw in [('people',(source/files['accounts']).read_bytes()),('accounts',b'invalid'),('budgets',(source/files['people']).read_bytes())]:
  old=(root/'master-data.json').read_bytes()
  try:preview(root,kind,raw,'wrong.xlsx')
  except (ValueError,Exception):pass
  else:raise AssertionError('Wrong file accepted')
  assert (root/'master-data.json').read_bytes()==old
 a=preview(root,'people',(source/files['people']).read_bytes(),'people.xlsx');b=preview(root,'people',(source/files['people']).read_bytes(),'people.xlsx')
 commit(root,a['token'])
 try:commit(root,b['token'])
 except ValueError:pass
 else:raise AssertionError('Stale import accepted')
assert (ROOT/'master-data.json').read_bytes()==original
print('PASS wrong files, stale preview rejected; live data untouched')
