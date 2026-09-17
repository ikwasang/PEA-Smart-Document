from pathlib import Path
p=Path('prototype/app.js');s=p.read_text(encoding='utf-8');a=s.index('function linkBudget(');z=s.index('function attachPicker(',a)
s=s[:a]+'''function linkBudget(b,key,value){b[key]=value;if(!['budgetFile','network'].includes(key))return;const entry=master.budgetFiles.find(f=>key==='budgetFile'?f.code===value:f.networks.some(n=>n.code===value));if(entry){b.budgetFile=entry.code;if(key==='budgetFile'&&!entry.networks.some(n=>n.code===b.network))b.network=entry.networks.length===1?entry.networks[0].code:'';const network=entry.networks.find(n=>n.code===b.network);if(!(network?.expenses||entry.expenses).includes(b.expense))b.expense='';}else if(key==='budgetFile'){b.network='';}else{b.budgetFile='';}}
function optionsFor(input){const id=input.dataset.options;let list=Array.from(document.getElementById(id)?.options||[]).map(o=>({value:o.value,label:o.label||o.value}));const field=input.closest('fieldset'),file=field?.querySelector('[data-options=budgetFile-options]')?.value,entry=master.budgetFiles.find(f=>f.code===file);if(id==='network-options'&&file)list=(entry?.networks||[]).map(n=>({value:n.code,label:n.code+' — '+n.name}));if(id==='expense-options'&&entry){const selected=field?.querySelector('[data-options=network-options]')?.value,network=entry.networks.find(n=>n.code===selected);list=(network?.expenses||entry.expenses).map(v=>({value:v,label:v}));}return list;}
''' +s[z:]
s=s.replace("master.budgetFiles.map(x=>[x.network,x.network+' — '+x.code])","master.budgetFiles.flatMap(x=>x.networks.map(n=>[n.code,n.code+' — '+x.code+' — '+n.name]))")
p.write_text(s,encoding='utf-8')
p=Path('template-review/refine_pdf.py');s=p.read_text(encoding='utf-8');a=s.index('cy=708');z=s.index("y=indented('จึงเรียน",a)
s=s[:a]+'''cy=708
for i,(name,role) in enumerate(committee):
 label=str(i+1)+'. '+name+'  '+positions.get(name,'ตำแหน่ง ................................')
 size=15
 while pdfmetrics.stringWidth(label,'PSK',size)>335 and size>10:size-=.25
 text(135,cy,label,size)
 text(478,cy,role,13)
 cy-=27
''' +s[z:];p.write_text(s,encoding='utf-8')
