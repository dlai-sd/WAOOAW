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

  // Missions definitions with investor-ready copy
  const MISSIONS = {
    customer: {
      title: 'Healthcare Provider Acquires Social Media Agent',
      milestones: [
        { id: 'marketplace_select', title: 'Browse Marketplace', desc: 'Customer discovers Social Media Agent with 4.8★ rating' },
        { id: 'trial_start', title: 'Start 7-Day Trial', desc: 'Zero-risk trial activated — customer keeps all deliverables' },
        { id: 'task_assign', title: 'Assign First Task', desc: 'Customer submits content brief: "Telehealth expansion strategy"' },
        { id: 'outline', title: 'Agent Produces Outline', desc: 'AI generates content strategy within 2 minutes (free-tier model)' },
        { id: 'drafts', title: 'Platform Drafts Generated', desc: 'Instagram, YouTube, LinkedIn drafts delivered — platform-optimized' },
        { id: 'review', title: 'Customer Reviews', desc: 'Customer reviews drafts, requests edits, approves final versions' },
        { id: 'schedule_post', title: 'Agent Schedules Posts', desc: 'Content auto-scheduled across platforms with optimal timing' }
      ]
    },
    creator: {
      title: 'CoE Factory Manufactures New Agent',
      milestones: [
        { id: 'propose', title: 'Agent Proposal', desc: 'DomainOnboard proposes market-validated agent template' },
        { id: 'vision_review', title: 'Vision Evaluation', desc: 'Vision analyzes market fit, salary benchmarks, demand signals' },
        { id: 'manufacturing', title: 'Build Pipeline', desc: 'Automated code generation, containerization, documentation' },
        { id: 'qa', title: 'Quality Assurance', desc: 'Unit tests, integration tests, performance benchmarks — all passed' },
        { id: 'attest', title: 'Compliance Attestation', desc: 'Vision + Security sign manifest (ed25519 cryptographic proof)' },
        { id: 'publish', title: 'Marketplace Publish', desc: 'Agent goes live — available for customer trials immediately' }
      ]
    },
    service: {
      title: 'Enterprise Incident Management',
      milestones: [
        { id: 'detect', title: 'Incident Detected', desc: 'Agent reports task failure — telemetry triggers L1 triage' },
        { id: 'triage', title: 'L1 Automated Triage', desc: 'Rule-based L1 agent attempts quick fix (cache refresh, retry logic)' },
        { id: 'escalate', title: 'L2/L3 Escalation', desc: 'Issue escalates to specialized L2 (diagnostics) and L3 (infrastructure)' },
        { id: 'resolve', title: 'Resolution & Audit', desc: 'Root cause identified, fix deployed, full audit trail captured' }
      ]
    },
    platform: {
      title: 'Enterprise Deployment at Scale',
      milestones: [
        { id: 'certified', title: 'Agent Certification', desc: 'Security scan passed, compliance badges issued (SOC2, GDPR)' },
        { id: 'configure', title: 'Runtime Configuration', desc: 'Prewarm pool size, rate limits, quota management configured' },
        { id: 'prewarm', title: 'Prewarm Pool Active', desc: 'Warm agent instances ready — zero-latency customer onboarding' },
        { id: 'monitor', title: 'Observability Live', desc: 'Telemetry streaming, billing meters active, SLA monitoring enabled' }
      ]
    }
  };

  let currentRun = null;
  let selectedMission = 'customer'; // Default selection

  // Mission selection
  document.querySelectorAll('.mission[data-mission]').forEach(card => {
    card.addEventListener('click', () => {
      // Remove previous selection
      document.querySelectorAll('.mission').forEach(m => m.classList.remove('selected'));
      // Mark as selected
      card.classList.add('selected');
      selectedMission = card.getAttribute('data-mission');
      // Clear timeline if different mission
      if(!currentRun || currentRun.missionId !== selectedMission) {
        renderTimeline(selectedMission);
      }
    });
  });

  // Initialize first mission as selected
  const firstMission = document.querySelector('.mission[data-mission]');
  if(firstMission) {
    firstMission.classList.add('selected');
    renderTimeline(selectedMission);
  }

  // UI rendering & state sync
  function refreshUI() {
    if (budgetDisplay) budgetDisplay.textContent = `$${(state.budget/100).toFixed(2)}`;
    if (xpDisplay) xpDisplay.textContent = state.xp;
    if (trialInfo) {
      if (state.trial && state.trial.active) { trialInfo.classList.remove('hidden'); if (trialDays) trialDays.textContent = state.trial.days; }
      else { trialInfo.classList.add('hidden'); }
    }
    if (factoryLog) {
      factoryLog.innerHTML = (state.factoryLogs||[]).map(l=>`<div style="padding:6px 4px;border-bottom:1px dashed rgba(255,255,255,0.02)">${l}</div>`).join('');
      // Auto-scroll to bottom
      factoryLog.scrollTop = factoryLog.scrollHeight;
    }
    if (incidentLog) incidentLog.innerHTML = (state.incidents||[]).slice().reverse().map(i=>`<div style="padding:8px;border-radius:8px;margin-bottom:8px;background:linear-gradient(90deg, rgba(255,20,147,0.03), rgba(122,43,255,0.02))"><div style="display:flex;justify-content:space-between"><strong>${i.title}</strong><span style="color:var(--muted)">${i.level}</span></div><div style="color:var(--muted);margin-top:6px">${i.status}</div></div>`).join('');
    if (instancesDiv) instancesDiv.innerHTML = (state.instances||[]).map(inst=>`<div class="instance"><div style="font-weight:700">${inst.name}</div><div style="font-size:12px;color:var(--muted)">Agent: ${inst.agent}</div><div style="font-size:12px;color:var(--muted)">Status: ${inst.status}</div></div>`).join('');
    if (orchestralLog) {
      orchestralLog.innerHTML = (state.orchestraLog||[]).slice().reverse().map(e=>`<div style="padding:6px;border-bottom:1px dashed rgba(255,255,255,0.02)">${e}</div>`).join('');
      // Auto-scroll to bottom
      orchestralLog.scrollTop = orchestralLog.scrollHeight;
    }
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

  function showMilestone(missionId, idx){
    if (!milestoneCard) return;
    const ms = MISSIONS[missionId].milestones[idx];
    if(!ms) return;
    document.querySelectorAll('.milestone').forEach(n=>n.classList.remove('active'));
    const active = document.querySelector(`.milestone[data-idx='${idx}']`);
    if(active) {
      active.classList.add('active');
      try{
        active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      } catch(e){ active.scrollIntoView(); }
    }
    milestoneCard.innerHTML = `<div style="font-weight:700;color:var(--accent-2)">${ms.title}</div><div style="margin-top:6px;color:var(--muted)">${ms.desc}</div><div style="margin-top:10px;font-size:12px;color:var(--muted)">Action: ${ms.id}</div>`;
  }

  // Mission execution mapping
  async function runMilestoneAction(missionId, idx){ const ms = MISSIONS[missionId].milestones[idx]; if(!ms) return; state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push(`✓ ${missionId.toUpperCase()}: ${ms.title}`); notifyOrchestration(`mission.${missionId}.${ms.id}`); refreshUI(); switch(ms.id){ case 'marketplace_select': state.factoryLogs.push('👁 Customer browsing marketplace — agent rating 4.8★ (1,247 reviews)'); break; case 'trial_start': state.trial={active:true,days:7}; addXP(5); state.factoryLogs.push('✅ 7-day trial activated (caps: 50 tasks, ₹8,000/mo value)'); break; case 'task_assign': await createTaskSample('Telehealth expansion strategy for healthcare providers',['youtube','instagram','linkedin']); break; case 'outline': await tick(600); state.factoryLogs.push('✓ AI outline generated in 87 seconds (free-tier model)'); addXP(3); break; case 'drafts': await tick(800); state.factoryLogs.push('✓ Platform-optimized drafts delivered: Instagram (Reels), YouTube (8min), LinkedIn (carousel)'); addXP(6); break; case 'review': await tick(500); state.factoryLogs.push('📝 Customer reviewed drafts, requested 2 edits — agent revised in real-time'); addXP(4); break; case 'schedule_post': await tick(700); state.factoryLogs.push('📅 Content auto-scheduled: Instagram (Tue 9am), YouTube (Thu 6pm), LinkedIn (Wed 11am)'); addXP(6); break; case 'propose': state.factoryLogs.push('🏭 DomainOnboard proposed: "Healthcare Social Media Agent" (market demand: HIGH)'); addXP(8); break; case 'vision_review': await tick(900); state.factoryLogs.push('🔍 Vision analyzing... Market fit: 94%, Avg salary: ₹12,500/mo, ROI: 3.2x'); addXP(10); break; case 'manufacturing': await tick(1000); state.factoryLogs.push('⚙️ Factory build pipeline running: code gen, containerization, docs — ETA 18 minutes'); addXP(10); break; case 'qa': await tick(900); state.factoryLogs.push('✅ QA passed: 147 unit tests, 23 integration tests, 0 vulnerabilities (Snyk scan)'); addXP(12); break; case 'attest': await tick(600); state.factoryLogs.push('🔐 Vision + Security attestation: ed25519 signature verified, manifest signed'); addXP(8); break; case 'publish': state.publishedAgents=state.publishedAgents||[]; state.publishedAgents.push('healthcare-social-media-agent'); state.instances=state.instances||[]; state.instances.push({name:'hsm-agent-001',agent:'healthcare-social-media-agent',status:'prewarm'}); addXP(18); state.factoryLogs.push('🚀 Agent published to marketplace — now available for customer trials'); break; case 'detect': state.incidents=state.incidents||[]; state.incidents.push({id:randId('inc'),title:'Content generation timeout (429)',level:'L1',status:'open'}); addXP(4); break; case 'triage': await tick(700); state.factoryLogs.push('🔧 L1 triage: cache refresh attempted, retry logic executed'); break; case 'escalate': await tick(900); state.factoryLogs.push('⚠️ Escalated to L2 (diagnostics) → L3 (infrastructure) for root cause analysis'); break; case 'resolve': await tick(800); state.factoryLogs.push('✅ Incident resolved: rate limit increased, caching layer optimized — SLA maintained'); addXP(10); break; case 'certified': state.factoryLogs.push('🏅 Agent certified: SOC2, GDPR compliant, security badges issued'); addXP(8); break; case 'configure': state.factoryLogs.push('⚙️ Runtime config: prewarm pool=5, max tasks/min=100, quota=1000 req/hr'); addXP(4); break; case 'prewarm': state.factoryLogs.push('🔥 Prewarm pool active: 5 warm instances ready for zero-latency onboarding'); addXP(6); break; case 'monitor': state.factoryLogs.push('📊 Observability live: Prometheus metrics, Grafana dashboards, billing meters streaming'); addXP(6); break; default: state.factoryLogs.push(`✓ Milestone ${ms.id} executed`); }
    refreshUI(); }

  async function createTaskSample(title, platforms){ const id = randId('task'); const task = { id, title, platforms, status:'queued', createdAt:Date.now(), outline:null, revisions:0 }; state.tasks = state.tasks||[]; state.tasks.push(task); state.factoryLogs.push(`📝 Task created: "${title}" (platforms: ${platforms.join(', ')})`); refreshUI(); await awaitOutline(task); }
  function awaitOutline(task){ return new Promise(resolve=>{ setTimeout(()=>{ task.status='outlining'; task.outline=`Content strategy outline: Hook → Problem → Solution → CTA (optimized for ${task.platforms.join('/')})`; state.factoryLogs.push(`✓ Content outline completed for task ${task.id}`); refreshUI(); setTimeout(()=>{ task.status='drafts_ready'; task.drafts = task.platforms.map(p=>({platform:p,text:`${p} draft: Platform-optimized, engagement-focused, SEO keywords included`})); state.factoryLogs.push(`✓ All platform drafts delivered — ready for customer review`); refreshUI(); resolve(); },900); },600); }); }

  // Play & Step logic with status feedback
  function showStatus(icon, message){
    const banner = document.getElementById('statusBanner');
    const iconEl = document.getElementById('statusIcon');
    const msgEl = document.getElementById('statusMessage');
    if(banner && iconEl && msgEl){
      iconEl.textContent = icon;
      msgEl.textContent = message;
      banner.classList.remove('hidden');
      setTimeout(()=>banner.classList.add('hidden'), 3000);
    }
  }
  
  async function playMissionAuto(missionId){ 
    if (currentRun && currentRun.playing) return; 
    showStatus('🚀', `Starting ${MISSIONS[missionId].title}...`);
    renderTimeline(missionId); 
    currentRun = { missionId, index:0, auto:true, playing:true }; 
    const steps = MISSIONS[missionId].milestones.length; 
    for(let i=0;i<steps;i++){ 
      if(!currentRun||!currentRun.playing) break; 
      showMilestone(missionId,i); 
      await runMilestoneAction(missionId,i); 
      await tick(1200); 
      currentRun.index = i+1; 
    } 
    if(currentRun) currentRun.playing=false; 
    addXP(20); 
    confettiBurst(40); 
    showStatus('🎉', 'Mission completed successfully!');
    currentRun=null; 
  }
  async function stepMission(missionId){ 
    if(!currentRun){ 
      showStatus('👣', `Stepping through ${MISSIONS[missionId].title}...`);
      renderTimeline(missionId); 
      currentRun={missionId,index:0,auto:false,playing:false}; 
    } 
    const i = currentRun.index||0; 
    if(i>=MISSIONS[missionId].milestones.length){ 
      showStatus('✅', 'All steps completed!');
      currentRun=null; 
      return; 
    } 
    showMilestone(missionId,i); 
    await runMilestoneAction(missionId,i); 
    currentRun.index=i+1; 
  }
  function abortMission(){ 
    showStatus('🛑', 'Mission aborted');
    currentRun=null; 
  }

  // Wiring mission buttons - Updated for selection
  const btnPlaySelected = document.getElementById('btnPlaySelected');
  const btnStepSelected = document.getElementById('btnStepSelected');

  if(btnPlaySelected) btnPlaySelected.addEventListener('click', () => {
    if(selectedMission) playMissionAuto(selectedMission).catch(()=>{});
  });
  
  if(btnStepSelected) btnStepSelected.addEventListener('click', () => {
    if(selectedMission) stepMission(selectedMission).catch(()=>{});
  });
  
  if(btnAbort) btnAbort.addEventListener('click', () => { abortMission(); });

  // Factory controls
  if(btnCreateAgentDef) btnCreateAgentDef.addEventListener('click',()=>{ const name = (newAgentName && newAgentName.value && newAgentName.value.trim()) || `specialized-agent-${Math.random().toString(36).slice(2,6)}`; state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push(`🏭 New agent proposal: "${name}" submitted to DomainOnboard for market analysis`); state.factoryLogs.push(`🔍 Vision queued for market fit evaluation (demand, pricing, competition)`); addXP(8); refreshUI(); });
  if(btnRunFactory) btnRunFactory.addEventListener('click',async()=>{ state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push('⚙️ Factory pipeline initiated — CoE agents collaborating on agent build'); refreshUI(); gsap.fromTo('#coe-domain',{y:-6},{y:0,duration:0.6,repeat:3,yoyo:true}); gsap.fromTo('#coe-vision',{y:-6,opacity:0.9},{y:0,duration:0.5,repeat:4,yoyo:true}); await tick(600); state.factoryLogs.push('✓ DomainOnboard: Role template generated, market analysis complete (demand score: 87/100)'); refreshUI(); await tick(900); state.factoryLogs.push('🔍 Vision: Analyzing market fit, salary benchmarks (₹8k-15k/mo), customer profiles...'); refreshUI(); await tick(1200); state.factoryLogs.push('✅ Vision: Approved — market validated, attestation signed (ed25519 cryptographic proof)'); refreshUI(); await tick(1200); state.factoryLogs.push('✓ TestAgent: 142 unit tests passed, 31 integration tests passed, performance benchmarks met'); await tick(800); state.factoryLogs.push('🔒 SecurityAgent: Vulnerability scan complete — 0 critical, 0 high, 2 low (accepted)'); await tick(700); state.factoryLogs.push('📦 PackagingAgent: Container image built (342 MB), API docs generated, README published'); await tick(600); state.factoryLogs.push('🏅 Factory: Agent certified and ready for marketplace deployment'); const agentName = `healthcare-smm-agent-${Math.random().toString(36).slice(2,4)}`; state.publishedAgents = state.publishedAgents||[]; state.publishedAgents.push(agentName); state.instances = state.instances||[]; state.instances.push({name:`${agentName}-inst-001`,agent:agentName,status:'prewarm'}); addXP(30); confettiBurst(30); refreshUI(); });

  // Incidents
  if(btnGenIncident) btnGenIncident.addEventListener('click',()=>{ const id = randId('inc'); const incident = { id, title: 'Agent task timeout (HTTP 429)', level: 'L1', status: 'open', createdAt:Date.now() }; state.incidents = state.incidents||[]; state.incidents.push(incident); state.factoryLogs = state.factoryLogs||[]; state.factoryLogs.push('⚠️ Incident detected: Agent task timeout (rate limit exceeded)'); addXP(4); refreshUI(); escalateIncident(incident); });
  function escalateIncident(incident){ setTimeout(()=>{ incident.status='L1 triage in progress'; state.factoryLogs.push(`🔧 L1 triage on ${incident.id}: cache refresh, retry logic executed`); refreshUI(); setTimeout(()=>{ incident.level='L2'; incident.status='escalated to L2'; state.factoryLogs.push(`↑ Escalated to L2 diagnostics: analyzing rate limits, quota usage`); refreshUI(); setTimeout(()=>{ incident.level='L3'; incident.status='escalated to L3'; state.factoryLogs.push(`↑ Escalated to L3 infrastructure: investigating API gateway, load balancers`); refreshUI(); setTimeout(()=>{ incident.status='resolved'; incident.resolvedAt=Date.now(); state.factoryLogs.push(`✅ Incident ${incident.id} resolved: rate limit increased, caching optimized, SLA maintained`); addXP(12); refreshUI(); confettiBurst(8); },1600); },1200); },1000); },800); }

  function notifyOrchestration(msg){ state.orchestraLog = state.orchestraLog||[]; const stamp = new Date().toLocaleTimeString(); state.orchestraLog.push(`${stamp} — ${msg}`); refreshUI(); }

  // Reset / export
  const btnReset = document.getElementById('btnReset'); const btnExport = document.getElementById('btnExport');
  if(btnReset) btnReset.addEventListener('click',()=>{ if(!confirm('Reset sandbox to default state?')) return; localStorage.removeItem(STORAGE_KEY); state = structuredClone(DEFAULT); refreshUI(); });
  if(btnExport) btnExport.addEventListener('click',()=>{ const dataStr = JSON.stringify(state,null,2); const blob = new Blob([dataStr],{type:'application/json'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download='waooaw_sandbox_state.json'; a.click(); URL.revokeObjectURL(url); });

  // Init
  gsap.fromTo('.panel',{y:12,opacity:0},{y:0,opacity:1,duration:0.9,stagger:0.06,ease:'power3.out'});
  if(!state.factoryLogs || !state.factoryLogs.length){ state.factoryLogs = ['👋 Welcome to WAOOAW Interactive Demo — Experience how AI agents earn your business through risk-free trials.']; addXP(12); refreshUI(); }

})();
