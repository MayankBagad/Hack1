const out = (id, data) => document.getElementById(id).textContent = JSON.stringify(data, null, 2);
const dt = (days) => new Date(Date.now() + days*86400000).toISOString();

async function api(url, options={}) {
  const res = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options});
  let data;
  try { data = await res.json(); } catch { data = {status: res.status}; }
  if (!res.ok) throw data;
  return data;
}

async function checkHealth(){ try{ out('healthOut', await api('/health')); }catch(e){ out('healthOut', e);} }
async function registerUser(){
  try {
    const body = {name:uName.value,email:uEmail.value,phone:uPhone.value,role:uRole.value};
    out('registerOut', await api('/auth/register',{method:'POST',body:JSON.stringify(body)}));
  } catch(e){ out('registerOut', e); }
}
async function verifyOtp(){ try{ out('verifyOut', await api('/auth/verify-otp',{method:'POST',body:JSON.stringify({user_id:+otpUserId.value,otp:'123456'})})); }catch(e){ out('verifyOut', e);} }
async function approveStudent(){ try{ out('verifyOut', await api(`/admin/verification/${+otpUserId.value}`,{method:'PATCH',body:JSON.stringify({status:'APPROVED'})})); }catch(e){ out('verifyOut', e);} }
async function createHackathon(){
  try {
    const body={title:hTitle.value,description:hDesc.value,registration_deadline:dt(2),round1_deadline:dt(3),final_deadline:dt(4)};
    out('hackOut', await api('/admin/hackathons',{method:'POST',body:JSON.stringify(body)}));
  } catch(e){ out('hackOut', e); }
}
async function createPS(){
  try { out('psOut', await api(`/admin/hackathons/${+psHackId.value}/problem-statements`,{method:'POST',body:JSON.stringify({title:psTitle.value,description:psDesc.value})})); }
  catch(e){ out('psOut', e); }
}
async function createTeam(){
  try {
    const body={hackathon_id:+tHackId.value,name:tName.value,captain_id:+tCaptain.value,member_ids:[],problem_statement_id:+tPS.value};
    out('teamOut', await api('/teams',{method:'POST',body:JSON.stringify(body)}));
  } catch(e){ out('teamOut', e); }
}
async function submitRound1(){
  try { out('subOut', await api('/submissions',{method:'POST',body:JSON.stringify({team_id:+sTeam.value,round:'ROUND1',ppt_link:sPpt.value})})); }
  catch(e){ out('subOut', e); }
}
async function addCriterionAndScore(){
  try {
    const c = await api('/admin/evaluation-criteria',{method:'POST',body:JSON.stringify({hackathon_id:+cHack.value,round:'ROUND1',name:cName.value,weight:+cWeight.value})});
    const s = await api('/judge/scores',{method:'POST',body:JSON.stringify({team_id:+scTeam.value,round:'ROUND1',judge_id:+scJudge.value,criterion_id:c.id,score:+scVal.value})});
    out('scoreOut', {criterion:c,score:s});
  } catch(e){ out('scoreOut', e); }
}
async function loadLeaderboard(){
  try { out('leaderOut', await api(`/admin/leaderboard?hackathon_id=${+lHack.value}&round_name=ROUND1`)); }
  catch(e){ out('leaderOut', e); }
}
async function genAndScan(){
  try {
    const q = await api('/qr/generate',{method:'POST',body:JSON.stringify({user_id:+qUser.value,hackathon_id:+qHack.value,purpose:'LUNCH',valid_from:new Date(Date.now()-60000).toISOString(),valid_to:new Date(Date.now()+3600000).toISOString()})});
    const s = await api('/scan',{method:'POST',body:JSON.stringify({token:q.token,scanner_id:+qScanner.value})});
    out('qrOut',{qr:q,scan:s});
  } catch(e){ out('qrOut',e); }
}
