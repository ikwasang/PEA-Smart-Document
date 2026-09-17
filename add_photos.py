from pathlib import Path
p=Path('prototype/index.html')
s=p.read_text(encoding='utf-8');s=s.replace('<datalist id="person-options">','<section class="card"><h2><span>05</span> รูปภาพประกอบ</h2><p class="hint">ไม่ใส่รูปก็ได้ หรือเลือกได้สูงสุด 3 รูป · JPG, PNG, WebP รูปละไม่เกิน 10 MB</p><label>เลือกรูปภาพ<input id="photos" type="file" accept="image/jpeg,image/png,image/webp" multiple></label><p id="photo-status" role="status"></p><div id="photo-list"></div></section>\n<datalist id="person-options">');p.write_text(s,encoding='utf-8')
p=Path('prototype/app.js');s=p.read_text(encoding='utf-8').replace('let budgets=[]','let photos=[],photoBusy=false,photoGeneration=0;\nlet budgets=[]').replace('function reset(){','function reset(){photoGeneration++;photos=[];renderPhotos();').replace('if(!form.reportValidity())return;','if(photoBusy){$(\'#message\').textContent=\'กรุณารอเตรียมรูปภาพให้เสร็จ\';return;}if(!form.reportValidity())return;').replace('data.items=items;','data.images=photos.map(p=>p.data);data.items=items;')
s=s.replace('reset();\n', '''function renderPhotos(){const host=$('#photo-list');host.replaceChildren();photos.forEach((p,i)=>{const card=document.createElement('div'),img=document.createElement('img'),name=document.createElement('p'),remove=document.createElement('button');img.src=p.data;img.alt='รูปที่ '+(i+1);name.textContent=p.name;remove.type='button';remove.textContent='ลบรูปที่ '+(i+1);remove.disabled=photoBusy;remove.onclick=()=>{photos.splice(i,1);invalidate();renderPhotos()};card.append(img,name,remove);host.append(card)});$('#photos').disabled=photoBusy||photos.length===3;$('#photo-status').textContent=photoBusy?'กำลังเตรียมรูปภาพ…':photos.length+' / 3 รูป';}
async function preparePhoto(file){if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>10*1024*1024)throw Error('กรุณาเลือกรูป JPG, PNG หรือ WebP ขนาดไม่เกิน 10 MB');const url=URL.createObjectURL(file);try{const img=new Image();img.src=url;await img.decode();const scale=Math.min(1,1200/Math.max(img.width,img.height)),canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(img.width*scale));canvas.height=Math.max(1,Math.round(img.height*scale));const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);return {name:file.name,data:canvas.toDataURL('image/jpeg',.85)};}finally{URL.revokeObjectURL(url)}}
$('#photos').onchange=async()=>{const files=Array.from($('#photos').files);$('#photos').value='';if(photos.length+files.length>3){$('#photo-status').textContent='เลือกได้สูงสุด 3 รูป กรุณาเลือกใหม่';return;}const generation=photoGeneration;photoBusy=true;invalidate();renderPhotos();try{const added=[];for(const file of files)added.push(await preparePhoto(file));if(generation===photoGeneration)photos.push(...added);}catch(e){$('#message').textContent=e.message;}finally{photoBusy=false;renderPhotos();}};
reset();
''');p.write_text(s,encoding='utf-8')
p=Path('prototype/style.css');p.write_text(p.read_text(encoding='utf-8')+'\n#photo-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}#photo-list img{width:100%;height:150px;object-fit:contain;background:#f3f4f8;border-radius:8px}#photo-list p{overflow-wrap:anywhere;font-size:17px}#photos{height:auto}\n',encoding='utf-8')
p=Path('prototype/server.py');s=p.read_text(encoding='utf-8').replace('import json,','import io\nfrom PIL import Image\nimport json,').replace(' return sub,vat', ''' images=d.get('images',[])
 if not isinstance(images,list) or len(images)>3:raise ValueError('ใส่รูปได้สูงสุด 3 รูป')
 for value in images:
  if not isinstance(value,str) or not value.startswith('data:image/jpeg;base64,') or len(value)>3000000:raise ValueError('รูปภาพไม่ถูกต้องหรือใหญ่เกินไป')
  try:
   raw=base64.b64decode(value.split(',',1)[1],validate=True)
   with Image.open(io.BytesIO(raw)) as im:
    if im.format!='JPEG' or max(im.size)>1200:raise ValueError('ขนาดรูปไม่ถูกต้อง')
    im.verify()
  except Exception:raise ValueError('อ่านรูปภาพไม่ได้ กรุณาเลือกรูปใหม่')
 return sub,vat''').replace('n>30000','n>9500000');p.write_text(s,encoding='utf-8')
p=Path('template-review/refine_pdf.py');s=p.read_text(encoding='utf-8');start=s.index("c.rect(149,176,259,174)");end=s.index("if data and len(data.get('budgets'",start)
s=s[:start]+'''photos=data.get('images',[]) if data else []
if photos:
 import base64,io
 from reportlab.lib.utils import ImageReader
 c.setStrokeColor(colors.black);c.rect(85,160,440,190);centered(305,329,'รูปภาพประกอบ',20)
 gap=10;slot=(420-gap*(len(photos)-1))/len(photos)
 for i,value in enumerate(photos):
  image=ImageReader(io.BytesIO(base64.b64decode(value.split(',',1)[1])))
  iw,ih=image.getSize();scale=min(slot/iw,140/ih);w,h=iw*scale,ih*scale
  c.drawImage(image,95+i*(slot+gap)+(slot-w)/2,175+(140-h)/2,width=w,height=h,mask='auto')
''' + s[end:];p.write_text(s,encoding='utf-8')
