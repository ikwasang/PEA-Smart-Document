(()=>{
const form=document.querySelector('#project-form,#budget-form,#form');if(!form)return;
let ready=false,token='',running=false;
const card=document.createElement('section');card.className='card sync-gate';
const button=document.createElement('button');button.type='button';button.className='sync-required';button.textContent='ดึงข้อมูลแฟ้มงานล่าสุด ก่อนเริ่มกรอก';
const status=document.createElement('p');status.setAttribute('role','status');status.textContent='ต้องกดดึงข้อมูลงบ I และ C ทุกครั้งก่อนกรอกเอกสาร';card.append(button,status);form.before(card);
function lock(){ready=false;token='';form.inert=true;status.textContent='กรุณากดดึงข้อมูลแฟ้มงานล่าสุดก่อนเริ่มกรอก';document.dispatchEvent(new Event('budget-sync-locked'));}
new MutationObserver(()=>{if(!ready&&!form.inert)form.inert=true;}).observe(form,{attributes:true,attributeFilter:['inert']});
const nativeFetch=window.fetch.bind(window);
window.fetch=(input,options={})=>{if(typeof input==='string'&&['/api/pdf','/api/budget/pdf','/api/project-budget/pdf'].includes(input)){const headers=new Headers(options.headers);headers.set('X-Budget-Sync',token);return nativeFetch(input,{...options,headers});}return nativeFetch(input,options);};
button.onclick=async()=>{if(running)return;lock();running=true;button.disabled=true;status.textContent='กำลังดึงงบ I และ C… กรุณารอ';try{const response=await nativeFetch('/api/project-budget/sync',{method:'POST'});const result=await response.json();if(!response.ok)throw Error(result.error);await window.applyBudgetMaster?.(result.data);token=result.token;ready=true;form.inert=false;status.textContent='อัปเดตแล้ว '+new Date(result.updatedAt).toLocaleString('th-TH')+' · '+result.counts.budgetFiles+' แฟ้มงาน · '+result.counts.networks+' โครงข่าย'+(result.warnings?.length?' · '+result.warnings.join(' · '):'');}catch(error){status.textContent=error.message+' — ยังไม่เปิดให้กรอก กรุณากดดึงข้อมูลอีกครั้ง';}finally{running=false;button.disabled=false;}};
window.resetBudgetGate=lock;lock();
})();
