from server import validate,WORK,PYTHON
from PIL import Image,ImageDraw
from pypdf import PdfReader
import json,base64,os,subprocess,copy
out=WORK/'prototype/test-output'
d=json.loads((out/'case-0.json').read_text(encoding='utf-8'))
photos=[]
for i,size in enumerate([(900,500),(450,800),(600,600)]):
 im=Image.new('RGB',size,['#b2d8ee','#e3c5ab','#bfdcc1'][i]);draw=ImageDraw.Draw(im);draw.rectangle((30,30,size[0]-30,size[1]-30),outline='black',width=8);draw.text((70,70),'TEST PHOTO '+str(i+1),fill='black',font_size=40)
 f=out/f'photo-{i+1}.jpg';im.save(f);photos.append('data:image/jpeg;base64,'+base64.b64encode(f.read_bytes()).decode())
for n in range(4):
 x=copy.deepcopy(d);x['images']=photos[:n];validate(x)
 f=out/'photos.json';f.write_text(json.dumps(x,ensure_ascii=False),encoding='utf-8');pdf=out/f'photos-{n}.pdf'
 env=os.environ.copy();env.update(PSDP_DATA=str(f),PSDP_PDF=str(pdf))
 subprocess.run([PYTHON,str(WORK/'template-review/refine_pdf.py')],cwd=WORK,env=env,check=True,capture_output=True)
 assert len(PdfReader(pdf).pages[-1].images)==n
for invalid in [photos+[photos[0]],['data:image/jpeg;base64,broken']]:
 x=copy.deepcopy(d);x['images']=invalid
 try:validate(x)
 except ValueError:pass
 else:raise AssertionError('Invalid photos accepted')
print('PASS: PDF 0/1/2/3 images; 4 images and malformed image rejected')
