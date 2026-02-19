const out = (id, data) => document.getElementById(id).textContent = JSON.stringify(data, null, 2);
const dt = d => new Date(Date.now() + d*86400000).toISOString();
let token = localStorage.getItem('token') || '';
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');

function headers() {
  const h = {'Content-Type':'application/json'};
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function api(url, options={}) {
  const res = await fetch(url, {headers: headers(), ...options});
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;
  return data;
}

function renderPanels() {
  sessionCard.classList.toggle('hidden', !currentUser);
  adminPanel.classList.toggle('hidden', !(currentUser && currentUser.role === 'ADMIN'));
  userPanel.classList.toggle('hidden', !currentUser || currentUser.role === 'ADMIN');
  whoami.textContent = currentUser ? `Logged in as ${currentUser.name} (${currentUser.role})` : 'Not logged in';
}

async function signup(){
  try {
    const body = {name:suName.value,email:suEmail.value,phone:suPhone.value,password:suPass.value,role:suRole.value};
    out('authOut', await api('/auth/signup',{method:'POST',body:JSON.stringify(body)}));
  } catch(e){ out('authOut', e); }
}

async function login(){
  try {
    const data = await api('/auth/login',{method:'POST',body:JSON.stringify({email:liEmail.value,password:liPass.value})});
    token = data.access_token;
    currentUser = data.user;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(currentUser));
    out('authOut', data);
    renderPanels();
  } catch(e){ out('authOut', e); }
}

function logout(){
  token=''; currentUser=null;
  localStorage.removeItem('token'); localStorage.removeItem('user');
  renderPanels();
}

async function loadMe(){ try{ out('meOut', await api('/auth/me')); }catch(e){ out('meOut', e);} }
async function verifyStudent(){ try{ out('vOut', await api(`/admin/verification/${+vUser.value}`,{method:'PATCH',body:JSON.stringify({status:vStatus.value})})); }catch(e){ out('vOut', e);} }
async function createHackathon(){ try{ out('hOut', await api('/admin/hackathons',{method:'POST',body:JSON.stringify({title:hTitle.value,description:hDesc.value,registration_deadline:dt(2),round1_deadline:dt(3),final_deadline:dt(4)})})); }catch(e){ out('hOut', e);} }
async function createPS(){ try{ out('psOut', await api(`/admin/hackathons/${+psH.value}/problem-statements`,{method:'POST',body:JSON.stringify({title:psT.value,description:psD.value})})); }catch(e){ out('psOut', e);} }
async function addCriterion(){ try{ out('cOut', await api('/admin/evaluation-criteria',{method:'POST',body:JSON.stringify({hackathon_id:+cH.value,round:'ROUND1',name:cN.value,weight:+cW.value})})); }catch(e){ out('cOut', e);} }
async function generateQr(){ try{ out('qOut', await api('/qr/generate',{method:'POST',body:JSON.stringify({user_id:+qU.value,hackathon_id:+qH.value,purpose:qP.value,valid_from:new Date(Date.now()-60000).toISOString(),valid_to:new Date(Date.now()+3600000).toISOString()})})); }catch(e){ out('qOut', e);} }
async function scanAnalytics(){ try{ out('aOut', await api(`/admin/scan-analytics?hackathon_id=${+aH.value}`)); }catch(e){ out('aOut', e);} }

async function uploadDocs(){ try{ out('docOut', await api('/verification/upload-documents',{method:'POST',body:JSON.stringify({college_id_path:docId.value,aadhaar_masked:docAa.value,selfie_path:docSf.value})})); }catch(e){ out('docOut', e);} }
async function faceMatch(){ try{ out('fmOut', await api('/verification/face-match',{method:'POST'})); }catch(e){ out('fmOut', e);} }
async function createTeam(){ try{ out('tOut', await api('/teams',{method:'POST',body:JSON.stringify({hackathon_id:+tH.value,name:tN.value,captain_id:+tC.value,member_ids:[],problem_statement_id:+tP.value})})); }catch(e){ out('tOut', e);} }
async function submitPpt(){ try{ out('sOut', await api('/submissions',{method:'POST',body:JSON.stringify({team_id:+sT.value,round:'ROUND1',ppt_link:sL.value})})); }catch(e){ out('sOut', e);} }

renderPanels();
