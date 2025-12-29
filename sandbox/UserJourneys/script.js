// WAOOAW Sandbox — Guided Missions & UserJourneys prototype (fixed and wired to current HTML)
// Ensures mission buttons and player controls work with minimal dependencies

(() => {
  // Utilities
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const el = (id) => document.getElementById(id);
  const randId = (p='id') => p + '-' + Math.random().toString(36).slice(2,9);

  // Initial state
  const DEFAULT = {
    budget: 1000, // cents => $10.00
    xp: 0,
    trial: { active: false, days: 7 },
    tasks: [],
    incidents: [],
    factoryLogs: [],
    instances: [],
    publishedAgents: [],
    orchestraLog: []
  };

  const STORAGE_KEY = 'waooaw_sandbox_v2';

  function loadState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) { saveState(DEFAULT); return structuredClone(DEFAULT); }
    return JSON.parse(raw);
  }
  function saveState(state) { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }

  let state = loadState();

  // DOM refs (IDs/classes used in index.html)
  const timelineEl = el('timeline');
  const milestoneCard = el('milestoneCard');
  const btnPlayAuto = el('btnPlayAuto');
  const btnStepNext = el('btnStepNext');
  const btnAbort = el('btnAbort');
  const factoryLog = el('factoryLog');
  const instancesDiv = el('instances');
  const orchestralLog = el('orchestralLog');
  const btnCreateAgentDef = el('btnCreateAgentDef');
  const btnRunFactory = el('btnRunFactory');
  const newAgentName = el('newAgentName');
  const btnGenIncident = el('btnGenIncident');
  const incidentLog = el('incidentLog');
  const budgetDisplay = el('budgetDisplay');
  const xpDisplay = el('xpDisplay');
  const trialInfo = el('trialInfo');
  const trialDays = el('trialDays');

  // Missions definitions
  const MISSIONS = {
    customer: {
      title: 'Doctor hires Social Media Agent',
      milestones: [
        { id: 'marketplace_select', title: 'Select Agent', desc: 'Customer finds Social Media Agent on marketplace' },
        { id: 'trial_start', title: 'Start 7-day Trial', desc: 'Trial enabled with caps' },
        { id: 'task_assign', title: 'Assign Task', desc: 'Customer submits theme / brief' },
        { id: 'outline', title: 'Outline Produced', desc: 'Agent returns outline (free model)' },
        { id: 'drafts', title: 'Drafts Ready', desc: 'Platform-specific drafts generated' },
        { id: 'review', title: 'Review & Approve', desc: 'Customer reviews drafts and approves' },
        { id: 'schedule_post', title: 'Schedule / Post', desc: 'Agent schedules or posts content' }
      ]
    },
    creator: {
      title: 'Factory builds a Social Media Agent',
      milestones: [
        { id: 'propose', title: 'Propose Agent', desc: 'DomainOnboard proposes new agent template' },
        { id: 'vision_review', title: 'Vision Review', desc: 'Vision evaluates market fit' },
        { id: 'manufacturing', title: 'Manufacturing', desc: 'Factory builds code & artifacts' },
        { id: 'qa', title: 'QA & Security', desc: 'Tests and security scans pass' },
        { id: 'attest', title: 'Attestation', desc: 'Vision & Compliance sign manifest' },
        { id: 'publish', title: 'Publish', desc: 'Agent available on marketplace' }
      ]
    },
    service: {
      title: 'Incident Escalation Flow',
      milestones: [
        { id: 'detect', title: 'Incident Detected', desc: 'Agent reports a failure' },
        { id: 'triage', title: 'L1 Triage', desc: 'Automated L1 tries quick fix' },
        { id: 'escalate', title: 'L2/L3 Escalation', desc: 'Issue escalates to specialized teams' },
        { id: 'resolve', title: 'Resolve & Audit', desc: 'Issue resolved with audit trail' }
      ]
    },
    platform: {
      title: 'Publish & Prewarm',
      milestones: [
        { id: 'certified', title: 'Certified Agent', desc: 'Agent has certification and badges' },
        { id: 'configure', title: 'Configure Runtime', desc: 'Set prewarm & quotas' },
        { id: 'prewarm', title: 'Prewarm Pool', desc: 'Warm pods ready' },
        { id: 'monitor', title: 'Monitoring', desc: 'Telemetry & billing live' }
      ]
    }
  };

  let currentRun = null;

  // UI rendering & state sync
  function refreshUI() {
    if (budgetDisplay) budgetDisplay.textContent = `$${(state.budget/100).toFixed(2)}`;
    if (xpDisplay) xpDisplay.textContent = state.xp;
    if (trialInfo) {
      if (state.trial && state.trial.active) { trialInfo.classList.remove('hidden'); if (trialDays) trialDays.textContent = state.trial.days; }
      else { trialInfo.classList.add('hidden'); }
    }
    if (factoryLog) factoryLog.innerHTML = (state.factoryLogs||[]).map(l=>`<div style="padding:6px 4px;border-bottom:1px dashed rgba(255,255,255,0.02)">${l}</div>`).join('');
    if (incidentLog) incidentLog.innerHTML = (state.incidents||[]).slice().reverse().map(i=>`<div style="padding:8px;border-radius:8px;margin-bottom:8px;background:linear-gradient(90deg, rgba(255,20,147,0.03), rgba(122,43,255,0.02))"><div style="display:flex;justify-content:space-between"><strong>${i.title}</strong><span style="color:var(--muted)">${i.level}</span></div><div style="color:var(--muted);margin-top:6px">${i.status}</div></div>`).join('');
    if (instancesDiv) instancesDiv.innerHTML = (state.instances||[]).map(inst=>`<div class="instance"><div style="font-weight:700">${inst.name}</div><div style="font-size:12px;color:var(--muted)">Agent: ${inst.agent}</div><div style="font-size:12px;color:var(--muted)">Status: ${inst.status}</div></div>`).join('');
    if (orchestralLog) orchestralLog.innerHTML = (state.orchestraLog||[]).slice().reverse().map(e=>`<div style="padding:6px;border-bottom:1px dashed rgba(255,255,255,0.02)">${e}</div>`).join('');
    saveState(state);
  }

  // Gamification
  function addXP(n){ state.xp = (state.xp||0) + n; if (xpDisplay) gsap.fromTo('#xpDisplay',{scale:0.9},{scale:1.08,duration:0.28,ease:'elastic.out(1,0.5)'}); refreshUI(); }
  function confettiBurst(p=60){ try{ confetti({ particleCount:p, spread:70, origin:{ y:0.3 } }); }catch(e){} }
  function tick(ms){ return new Promise(r=>setTimeout(r,ms)); }

  // Timeline rendering
  function renderTimeline(missionId){
    if (!timelineEl) return;
    const m = MISSIONS[missionId];
    timelineEl.innerHTML = '';
    if (!m) { timelineEl.innerHTML = '<div class="muted">Select a mission to view the timeline.</div>'; return; }
    m.milestones.forEach((ms,idx)=>{
      const d = document.createElement('div'); d.className = 'milestone'; d.dataset.idx = idx; d.innerHTML = `<div style="font-weight:700">${ms.title}</div><div style="font-size:12px;color:var(--muted)">${ms.desc}</div>`; timelineEl.appendChild(d);
    });
  }

  function showMilestone(missionId, idx){ if (!milestoneCard) return; const ms = MISSIONS[missionId].milestones[idx]; if(!ms) return; document.querySelectorAll('.milestone').forEach(n=>n.classList.remove('active')); const active = document.querySelector(`.milestone[data-idx='${idx}']`); if(active) active.classList.add('active'); milestoneCard.innerHTML = `<div style="font-weight:700;color:var(--accent-2)">${ms.title}</div><div style="margin-top:6px;color:var(--muted)">${ms.desc}</div><div style="margin-top:10px;font-size:12px;color:var(--muted)">Action: ${ms.id}</div>`; }

  // Mission execution mapping
  async function runMilestoneAction(missionId, idx){ const ms = MISSIONS[missionId].milestones[idx]; if(!ms) return; state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push(`Mission:${missionId} -> ${ms.title}`); notifyOrchestration(`mission.${missionId}.${ms.id}`); refreshUI(); switch(ms.id){ case 'marketplace_select': state.factoryLogs.push('Customer selects Social Media Agent in marketplace.'); break; case 'trial_start': state.trial={active:true,days:7}; addXP(5); state.factoryLogs.push('Trial started (7 days)'); break; case 'task_assign': await createTaskSample('How doctors can use telehealth to expand reach',['youtube','instagram']); break; case 'outline': await tick(600); state.factoryLogs.push('Agent produced outline (free model)'); addXP(3); break; case 'drafts': await tick(800); state.factoryLogs.push('Agent produced platform drafts'); addXP(6); break; case 'review': await tick(500); state.factoryLogs.push('Customer reviews and requests minor edits'); addXP(4); break; case 'schedule_post': await tick(700); state.factoryLogs.push('Agent schedules post for selected platforms'); addXP(6); break; case 'propose': state.factoryLogs.push('DomainOnboard proposed new agent template'); addXP(8); break; case 'vision_review': await tick(900); state.factoryLogs.push('Vision reviewing — approved'); addXP(10); break; case 'manufacturing': await tick(1000); state.factoryLogs.push('Factory building code & container image'); addXP(10); break; case 'qa': await tick(900); state.factoryLogs.push('Tests & security scans passed'); addXP(12); break; case 'attest': await tick(600); state.factoryLogs.push('Vision & Compliance attested manifest (sig simulated)'); addXP(8); break; case 'publish': state.publishedAgents=state.publishedAgents||[]; state.publishedAgents.push('social-media-agent'); state.instances=state.instances||[]; state.instances.push({name:'social-media-agent-inst',agent:'social-media-agent',status:'idle'}); addXP(18); state.factoryLogs.push('Agent published to marketplace.'); break; case 'detect': state.incidents=state.incidents||[]; state.incidents.push({id:randId('inc'),title:'Content generation failed',level:'L1',status:'open'}); addXP(4); break; case 'triage': await tick(700); state.factoryLogs.push('L1 attempted automated fix'); break; case 'escalate': await tick(900); state.factoryLogs.push('Escalated to L2/L3'); break; case 'resolve': await tick(800); state.factoryLogs.push('Incident resolved and audited'); addXP(10); break; case 'certified': state.factoryLogs.push('Agent certified with badges (vision, security)'); addXP(8); break; case 'configure': state.factoryLogs.push('Platform configured runtime prewarm & quotas'); addXP(4); break; case 'prewarm': state.factoryLogs.push('Prewarm pool created (simulated)'); addXP(6); break; case 'monitor': state.factoryLogs.push('Monitoring & billing live'); addXP(6); break; default: state.factoryLogs.push(`Milestone ${ms.id} executed`); }
    refreshUI(); }

  async function createTaskSample(title, platforms){ const id = randId('task'); const task = { id, title, platforms, status:'queued', createdAt:Date.now(), outline:null, revisions:0 }; state.tasks = state.tasks||[]; state.tasks.push(task); state.factoryLogs.push(`Task created: "${title}"`); refreshUI(); await awaitOutline(task); }
  function awaitOutline(task){ return new Promise(resolve=>{ setTimeout(()=>{ task.status='outlining'; task.outline=`Outline for "${task.title}" — bullets: Hook / Problem / Solution / CTA`; state.factoryLogs.push(`Outline produced for task ${task.id}`); refreshUI(); setTimeout(()=>{ task.status='drafts_ready'; task.drafts = task.platforms.map(p=>({platform:p,text:`Draft for ${p} — polished`})); state.factoryLogs.push('Drafts ready'); refreshUI(); resolve(); },900); },600); }); }

  // Play & Step logic
  async function playMissionAuto(missionId){ if (currentRun && currentRun.playing) return; renderTimeline(missionId); currentRun = { missionId, index:0, auto:true, playing:true }; const steps = MISSIONS[missionId].milestones.length; for(let i=0;i<steps;i++){ if(!currentRun||!currentRun.playing) break; showMilestone(missionId,i); await runMilestoneAction(missionId,i); await tick(800); currentRun.index = i+1; } if(currentRun) currentRun.playing=false; addXP(20); confettiBurst(40); currentRun=null; }
  async function stepMission(missionId){ if(!currentRun){ renderTimeline(missionId); currentRun={missionId,index:0,auto:false,playing:false}; } const i = currentRun.index||0; if(i>=MISSIONS[missionId].milestones.length){ currentRun=null; return; } showMilestone(missionId,i); await runMilestoneAction(missionId,i); currentRun.index=i+1; }
  function abortMission(){ currentRun=null; }

  // Wiring mission buttons (data-action in index.html)
  document.querySelectorAll('[data-action][data-mission]').forEach(btn=>{
    btn.addEventListener('click',(e)=>{
      const action = btn.getAttribute('data-action');
      const mission = btn.getAttribute('data-mission');
      if(action==='play'){ playMissionAuto(mission).catch(()=>{}); }
      else if(action==='step'){ stepMission(mission).catch(()=>{}); }
    });
  });

  if(btnPlayAuto) btnPlayAuto.addEventListener('click',()=>{ const first = document.querySelector('[data-action="play"][data-mission]'); const m = first? first.getAttribute('data-mission') : 'customer'; playMissionAuto(m).catch(()=>{}); });
  if(btnStepNext) btnStepNext.addEventListener('click',()=>{ const first = document.querySelector('[data-action="step"][data-mission]'); const m = first? first.getAttribute('data-mission') : 'customer'; if(!currentRun){ renderTimeline(m); currentRun={missionId:m,index:0,auto:false,playing:false}; } stepMission(m).catch(()=>{}); });
  if(btnAbort) btnAbort.addEventListener('click',()=>{ abortMission(); });

  // Factory controls
  if(btnCreateAgentDef) btnCreateAgentDef.addEventListener('click',()=>{ const name = (newAgentName && newAgentName.value && newAgentName.value.trim()) || `agent-${Math.random().toString(36).slice(2,6)}`; state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push(`Agent "${name}" proposed by DomainOnboard.`); state.factoryLogs.push(`Event: propose -> Vision review queued.`); addXP(8); refreshUI(); });
  if(btnRunFactory) btnRunFactory.addEventListener('click',async()=>{ state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push('Factory run started — orchestrating CoE agents'); refreshUI(); gsap.fromTo('#coe-domain',{y:-6},{y:0,duration:0.6,repeat:3,yoyo:true}); gsap.fromTo('#coe-vision',{y:-6,opacity:0.9},{y:0,duration:0.5,repeat:4,yoyo:true}); await tick(600); state.factoryLogs.push('DomainOnboard produced role-template and market analysis'); refreshUI(); await tick(900); state.factoryLogs.push('Vision reviewing market fit & salary reports...'); refreshUI(); await tick(1200); state.factoryLogs.push('Vision: Approved ✅ — manifest attestation produced (ed25519 signature simulated).'); refreshUI(); await tick(1200); state.factoryLogs.push('TestAgent: unit/integration tests passed.'); await tick(800); state.factoryLogs.push('SecurityAgent: vulnerability scan passed.'); await tick(700); state.factoryLogs.push('PackagingAgent: built container image and docs.'); await tick(600); state.factoryLogs.push('Factory: Agent certified and ready for publish.'); const agentName = `social-media-agent-${Math.random().toString(36).slice(2,4)}`; state.publishedAgents = state.publishedAgents||[]; state.publishedAgents.push(agentName); state.instances = state.instances||[]; state.instances.push({name:`${agentName}-inst`,agent:agentName,status:'idle'}); addXP(30); confettiBurst(30); refreshUI(); });

  // Incidents
  if(btnGenIncident) btnGenIncident.addEventListener('click',()=>{ const id = randId('inc'); const incident = { id, title: 'Content generation failed', level: 'L1', status: 'open', createdAt:Date.now() }; state.incidents = state.incidents||[]; state.incidents.push(incident); state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push('Incident created: Content generation failure'); addXP(4); refreshUI(); escalateIncident(incident); });
  function escalateIncident(incident){ setTimeout(()=>{ incident.status='triaged by L1'; state.factoryLogs.push(`L1 triage on ${incident.id}`); refreshUI(); setTimeout(()=>{ incident.level='L2'; incident.status='escalated to L2'; state.factoryLogs.push(`Escalated to L2 for analysis`); refreshUI(); setTimeout(()=>{ incident.level='L3'; incident.status='escalated to L3 - infra'; state.factoryLogs.push(`Escalated to L3 - infra investigating`); refreshUI(); setTimeout(()=>{ incident.status='resolved'; incident.resolvedAt=Date.now(); state.factoryLogs.push(`Incident ${incident.id} resolved by L3`); addXP(12); refreshUI(); confettiBurst(8); },1600); },1200); },1000); },800); }

  function notifyOrchestration(msg){ state.orchestraLog = state.orchestraLog||[]; const stamp = new Date().toLocaleTimeString(); state.orchestraLog.push(`${stamp} — ${msg}`); refreshUI(); }

  // Reset / export
  const btnReset = document.getElementById('btnReset'); const btnExport = document.getElementById('btnExport');
  if(btnReset) btnReset.addEventListener('click',()=>{ if(!confirm('Reset sandbox to default state?')) return; localStorage.removeItem(STORAGE_KEY); state = structuredClone(DEFAULT); refreshUI(); });
  if(btnExport) btnExport.addEventListener('click',()=>{ const dataStr = JSON.stringify(state,null,2); const blob = new Blob([dataStr],{type:'application/json'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download='waooaw_sandbox_state.json'; a.click(); URL.revokeObjectURL(url); });

  // Init
  gsap.fromTo('.panel',{y:12,opacity:0},{y:0,opacity:1,duration:0.9,stagger:0.06,ease:'power3.out'});
  if(!state.factoryLogs || !state.factoryLogs.length){ state.factoryLogs = ['Welcome to WAOOAW sandbox. Use Missions to play guided journeys.']; addXP(12); refreshUI(); }

})();
