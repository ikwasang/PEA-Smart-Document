const documentType=document.createElement('select');
documentType.name='documentType';documentType.id='document-type';
for(const [value,label] of [['purchase','จัดซื้อ'],['hiring','จัดจ้าง']]){const o=document.createElement('option');o.value=value;o.textContent=label;documentType.append(o);}
const typeLabel=document.createElement('label');typeLabel.hidden=true;typeLabel.textContent='ประเภทเอกสาร';typeLabel.append(documentType);form.firstElementChild.querySelector('.grid').prepend(typeLabel);
const supervisorLabel=document.createElement('label');supervisorLabel.id='supervisor-field';supervisorLabel.textContent='ผู้ควบคุมงาน';
const supervisor=document.createElement('input');supervisor.name='supervisor';supervisor.maxLength=40;supervisor.setAttribute('list','person-options');supervisorLabel.append(supervisor);
form.elements.chair.closest('.grid').append(supervisorLabel);
const vendorLabel=form.elements.vendor.closest('label'),descriptionLabel=form.elements.description.closest('label');
function updateDocumentType(){const hiring=documentType.value==='hiring';document.querySelector('main h1').textContent=hiring?'จัดทำเอกสารจัดจ้าง':'จัดทำเอกสารจัดซื้อ';vendorLabel.firstChild.textContent=hiring?'ผู้รับจ้าง / บริษัท':'ผู้ขาย / บริษัท';descriptionLabel.firstChild.textContent=hiring?'รายละเอียดงานจ้าง':'รายละเอียดพัสดุ';supervisorLabel.hidden=!hiring;supervisor.required=hiring;supervisor.disabled=false;$('#download').download=hiring?'เอกสารจัดจ้าง.pdf':'เอกสารจัดซื้อ.pdf';$('#pdf').setAttribute('aria-label',hiring?'ตัวอย่างเอกสารจัดจ้าง':'ตัวอย่างเอกสารจัดซื้อ');}
const editorPage=document.querySelector('main');
const adminLink=document.createElement('a');adminLink.href='/admin';adminLink.className='admin-link';adminLink.textContent='จัดการข้อมูล';document.querySelector('header').append(adminLink);
const vendorReminder=document.createElement('section');vendorReminder.className='vendor-reminder';vendorReminder.setAttribute('aria-label','เอกสารประกอบการรับเงิน');
vendorReminder.innerHTML='<p class="vendor-bank-question">มีบัญชีธนาคารออมสิน หรือ ธ.ก.ส. ไหม?</p><ol><li>สำเนาใบทะเบียนภาษีมูลค่าเพิ่ม (ภ.พ.20) จากกรมสรรพากร <span>(ถ้าต้องเปิด vendor)</span></li><li>สำเนาหนังสือรับรองจากกรมพัฒนาธุรกิจการค้า ที่มีอายุไม่เกิน 1 เดือน <span>(ถ้าต้องเปิด vendor)</span></li><li>แบบคำขอรับโอนเงินธนาคาร หรือแบบขอรับเงินโอนอิเล็กทรอนิกส์</li><li>สำเนา Book Bank</li><li>สำเนาบัตรประชาชนผู้มีอำนาจ</li></ol><p class="vendor-certify">สำเนาทุกฉบับให้เซ็นสำเนาถูกต้อง</p>';
editorPage.querySelector('.heading').insertBefore(vendorReminder,document.getElementById('reset'));
const home=document.createElement('section');home.id='document-home';home.className='document-home';
home.innerHTML='<p class="eyebrow">PEA Smart Document Platform</p><h1>วันนี้ต้องการทำเอกสารอะไร?</h1><p>เลือกประเภทเอกสารเพื่อเริ่มกรอกข้อมูล</p><div class="document-choices"><button type="button" data-kind="purchase" disabled><span class="document-symbol">01</span><strong>เอกสารจัดซื้อ</strong><span>รายงานขอซื้อ และเอกสารตรวจรับพัสดุ</span><span class="choice-action">เลือกจัดซื้อ →</span></button><button type="button" data-kind="hiring" disabled><span class="document-symbol">02</span><strong>เอกสารจัดจ้าง</strong><span>รายงานขอจ้าง พร้อมผู้ควบคุมงานและตรวจรับ</span><span class="choice-action">เลือกจัดจ้าง →</span></button></div><p id="home-status" role="status">กำลังเปิดข้อมูล…</p><p class="hint">ข้อมูลร่วมใช้ร่างล่าสุด 1 ชุด สลับประเภทได้โดยไม่ต้องกรอกใหม่</p>';
editorPage.before(home);
const budgetChoices=document.createElement('section');budgetChoices.className='card';budgetChoices.innerHTML='<h2>ใบตัดงบ</h2><p>เลือกประเภทใบตัดงบที่ต้องการจัดทำ</p><div class="budget-home-actions"><a class="budget-home-link" href="/budget"><strong>ใบตัดงบทำการ →</strong><span>เพิ่มรายการได้ไม่จำกัด พร้อมตัวอย่าง PDF</span></a><a class="budget-home-link" href="/project-budget"><strong>ใบตัดงบแฟ้มงาน →</strong><span>เลือกงาน โครงข่าย และกิจกรรมจากข้อมูล Excel</span></a></div>';home.querySelector('.document-choices').after(budgetChoices);
const back=document.createElement('button');back.type='button';back.className='quiet';back.id='back-home';back.textContent='← กลับไปเลือกประเภทเอกสาร';editorPage.prepend(back);
let editingDocument=false;
function showHome(){window.resetBudgetGate?.();editingDocument=false;editorPage.hidden=true;home.hidden=false;document.title='PEA Smart Document';document.querySelector('.brand small').textContent='กฟส.พร้าว';window.scrollTo(0,0);home.querySelector('h1').setAttribute('tabindex','-1');home.querySelector('h1').focus();}
back.onclick=showHome;
home.querySelectorAll('[data-kind]').forEach(button=>{button.onclick=()=>{if(!draftReady)return;window.resetBudgetGate?.();editingDocument=true;documentType.value=button.dataset.kind;updateDocumentType();invalidate();home.hidden=true;editorPage.hidden=false;window.scrollTo(0,0);const heading=editorPage.querySelector('h1');heading.tabIndex=-1;heading.focus();};});
const updateFormType=updateDocumentType;
const hiringForms=document.createElement('section');hiringForms.id='hiring-forms';hiringForms.className='hiring-forms';hiringForms.hidden=true;
const formsHeading=document.createElement('h2');formsHeading.textContent='ดาวน์โหลดแบบฟอร์มประกอบการจัดจ้าง';hiringForms.append(formsHeading);
const formsList=document.createElement('div');formsList.className='hiring-forms-list';
for(const [file,label] of [['supervisor.docx','บันทึกผู้ควบคุมงานจ้าง'],['acceptance.docx','บันทึกตรวจรับงานจ้าง'],['conditions.pdf','เงื่อนไขประกอบใบสั่งจ้าง'],['bank-payment.pdf','แบบคำขอรับเงินผ่านธนาคาร'],['electronic-transfer.pdf','หนังสือแจ้งความประสงค์ขอรับเงินโอนอิเล็กทรอนิกส์'],['electronic-transfer-example.pdf','ตัวอย่างหนังสือแจ้งความประสงค์ขอรับเงินโอนอิเล็กทรอนิกส์']]){const a=document.createElement('a');a.href='/forms/'+file;a.download=label+(file.endsWith('.pdf')?'.pdf':'.docx');a.textContent=label;const type=document.createElement('span');type.textContent=file.endsWith('.pdf')?'PDF ↓':'Word ↓';a.append(type);formsList.append(a);}
hiringForms.append(formsList);editorPage.querySelector('.heading').after(hiringForms);
const purchaseForms=document.createElement('section');purchaseForms.id='purchase-forms';purchaseForms.className='hiring-forms';purchaseForms.hidden=true;
const purchaseFormsHeading=document.createElement('h2');purchaseFormsHeading.textContent='ดาวน์โหลดแบบฟอร์มประกอบการจัดซื้อ';purchaseForms.append(purchaseFormsHeading);
const purchaseFormsList=document.createElement('div');purchaseFormsList.className='hiring-forms-list';
for(const file of ['bank-payment.pdf','electronic-transfer.pdf','electronic-transfer-example.pdf'])purchaseFormsList.append(formsList.querySelector('a[href="/forms/'+file+'"]').cloneNode(true));
purchaseForms.append(purchaseFormsList);hiringForms.before(purchaseForms);
updateDocumentType=function(){updateFormType();const label=documentType.value==='hiring'?'เอกสารจัดจ้าง':'เอกสารจัดซื้อ';document.title=editingDocument?'PEA Smart Document — '+label:'PEA Smart Document';document.querySelector('.brand small').textContent=editingDocument?label+' · กฟส.พร้าว':'กฟส.พร้าว';home.querySelectorAll('[data-kind]').forEach(b=>b.disabled=!draftReady);$('#home-status').textContent=draftReady?'พร้อมใช้งาน · บันทึกร่างอัตโนมัติบนเครื่องนี้':$('#draft-status').textContent;};
documentType.addEventListener('change',()=>{updateDocumentType();invalidate();});
const updateWithForms=updateDocumentType;
updateDocumentType=function(){updateWithForms();hiringForms.hidden=documentType.value!=='hiring';purchaseForms.hidden=documentType.value!=='purchase';};
updateDocumentType();
// Shared navigation for both document forms and their previews.
(()=>{
 const button=document.createElement('button');
 button.type='button';button.className='back-to-top';
 button.textContent='↑ ขึ้นบนสุด';button.setAttribute('aria-label','เลื่อนขึ้นบนสุด');
 button.hidden=true;document.body.append(button);
 const update=()=>{button.hidden=window.scrollY<300;};
 window.addEventListener('scroll',update,{passive:true});
 button.addEventListener('click',()=>window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));
 update();
})();
