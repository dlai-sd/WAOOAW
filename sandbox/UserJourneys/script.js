// WAOOAW Sandbox — UserJourneys interactive prototype
// Uses localStorage to persist sandbox state. Has playful gamification and simulated pipelines.

(() => {
  // Utilities
  const $ = (sel) => document.querySelector(sel);
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
    publishedAgents: []
  };

  const STORAGE_KEY = 'waooaw_sandbox_v1';

  function loadState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) { saveState(DEFAULT); return structuredClone(DEFAULT); }
    return JSON.parse(raw);
  }
  function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  let state = loadState();

  // DOM references
  const budgetDisplay = el('budgetDisplay');
  const xpDisplay = el('xpDisplay');
  const roleSelector = el('roleSelector');
  const btnStartTrial = el('btnStartTrial');
  const btnSubscribe = el('btnSubscribe');
  const trialInfo = el('trialInfo');
  const trialDays = el('trialDays');
  const btnCreateTask = el('btnCreateTask');
  const taskTheme = el('taskTheme');
  const taskFeed = el('taskFeed');
  const btnCreateAgentDef = el('btnCreateAgentDef');
  const btnRunFactory = el('btnRunFactory');
  const factoryLog = el('factoryLog');
  const newAgentName = el('newAgentName');
  const btnGenIncident = el('btnGenIncident');
  const incidentLog = el('incidentLog');
  const instancesDiv = el('instances');
  const orchestralLog = el('orchestralLog');
  const btnReset = el('btnReset');
  const btnExport = el('btnExport');

  // Update UI from state
  function refreshUI() {
    budgetDisplay.textContent = `$${(state.budget/100).toFixed(2)}`;
    xpDisplay.textContent = state.xp;
    if (state.trial.active) {
      trialInfo.classList.remove('hidden');
      trialDays.textContent = state.trial.days;
      btnStartTrial.textContent = 'Trial Active';
      btnStartTrial.disabled = true;
    } else {
      trialInfo.classList.add('hidden');
      btnStartTrial.textContent = 'Start 7‑day Trial';
      btnStartTrial.disabled = false;
    }

    // tasks
    taskFeed.innerHTML = '';
    state.tasks.slice().reverse().forEach(t => {
      const d = document.createElement('div');
      d.className = 'task-card';
      d.style.padding = '10px';
      d.style.borderRadius = '8px';
      d.style.marginBottom = '8px';
      d.style.background = 'linear-gradient(90deg, rgba(255,255,255,0.01), rgba(255,255,255,0.005))';
      d.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>${t.title}</strong> <span style="color:var(--muted);font-size:12px">[${t.platforms.join(', ')}]</span></div>
        <div style="font-size:12px;color:var(--muted)">${t.status}</div>
      </div>
      <div style="margin-top:6px;font-size:13px;color:var(--muted)">${t.outline||''}</div>
      <div style="margin-top:8px;display:flex;gap:8px">
        <button class="btn ghost" data-id="${t.id}" data-action="view">View</button>
        <button class="btn primary" data-id="${t.id}" data-action="upgrade">Upgrade→Premium</button>
      </div>`;
      taskFeed.appendChild(d);
    });

    // factory log
    factoryLog.innerHTML = state.factoryLogs.map(l => `<div style="padding:6px 4px;border-bottom:1px dashed rgba(255,255,255,0.02)">${l}</div>`).join('');

    // incidents
    incidentLog.innerHTML = state.incidents.slice().reverse().map(i => `<div style="padding:8px;border-radius:8px;margin-bottom:8px;background:linear-gradient(90deg, rgba(255,20,147,0.03), rgba(122,43,255,0.02))">
      <div style="display:flex;justify-content:space-between"><strong>${i.title}</strong><span style="color:var(--muted)">${i.level}</span></div>
      <div style="color:var(--muted);margin-top:6px">${i.status}</div>
    </div>`).join('');

    // instances
    instancesDiv.innerHTML = state.instances.map(inst => {
      return `<div class="instance">
        <div style="font-weight:700">${inst.name}</div>
        <div style="font-size:12px;color:var(--muted)">Agent: ${inst.agent}</div>
        <div style="font-size:12px;color:var(--muted)">Status: ${inst.status}</div>
      </div>`;
    }).join('');

    // orchestral log
    orchestralLog.innerHTML = (state.orchestraLog||[]).slice().reverse().map(e => `<div style="padding:6px;border-bottom:1px dashed rgba(255,255,255,0.02)">${e}</div>`).join('');

    saveState(state);
  }

  // Init UI
  refreshUI();

  // Gamification helpers
  function addXP(n){
    state.xp += n;
    xpAnim();
    refreshUI();
  }
  function spendBudget(cents){
    if (state.budget < cents) return false;
    state.budget -= cents; refreshUI(); return true;
  }
  function xpAnim(){
    gsap.fromTo('#xpDisplay',{scale:0.9},{scale:1.08,duration:0.28, ease:'elastic.out(1,0.5)'});
  }

  // Role switch influences helper hints (mild)
  roleSelector.addEventListener('change', (e)=>{
    const role = e.target.value;
    const hint = {
      explorer: 'You are exploring. Try starting a trial and running the factory.',
      customer: 'Customer: start a trial and assign a content task to the Social Media Agent.',
      creator: 'Creator: propose a new agent and run the Factory to see attestations.',
      service: 'Service Ops: create incidents and practice escalation.',
      platform: 'Platform Builder: monitor budget, publish agents, manage prewarm settings.'
    }[role] || '';
    // small hint via fab glow
    gsap.fromTo('.topbar',{backgroundColor:'rgba(255,255,255,0.01)'},{backgroundColor:'rgba(255,255,255,0.02)',duration:0.6,yoyo:true,repeat:1});
    console.log('role hint:', hint);
  });

  // Trial / subscription
  btnStartTrial.addEventListener('click', ()=>{
    state.trial.active = true;
    state.trial.days = 7;
    state.factoryLogs.push(`Trial started for Social Media Agent (7 days).`);
    addXP(20);
    confettiBurst();
    refreshUI();
  });
  btnSubscribe.addEventListener('click', ()=>{
    // subscribe: allocate budget for premium skills automatically (example)
    if (state.budget < 0) { alert('Please add budget'); return; }
    state.factoryLogs.push('Subscription completed for Social Media Agent. Premium enabled on account.');
    // toggle premium access on published agent instances, simulated
    state.publishedAgents.push('social-media-agent');
    state.instances.push({name:`${agentName}-inst`, agent:agentName, status:'idle'});
    addXP(10);
    confettiBurst();
    refreshUI();
  });

  // Task creation & pipeline simulation
  btnCreateTask.addEventListener('click', ()=>{
    const title = taskTheme.value.trim();
    if (!title) { alert('Please add a theme/brief'); return; }
    const platforms = Array.from(document.querySelectorAll('.platform-select input:checked')).map(i=>i.value);
    const id = randId('task');
    const task = { id, title, platforms, status:'queued', createdAt:Date.now(), outline:null, revisions:0 };
    state.tasks.push(task);
    state.factoryLogs.push(`Task created: "${title}"`);
    addXP(5);
    refreshUI();
    // Simulate processing: outline -> drafts -> ready for review
    simulateTaskProcessing(task);
  });

  function simulateTaskProcessing(task){
    // Stage 1: outline with free model (fast)
    setTimeout(()=> {
      task.status = 'outlining';
      task.outline = `Outline for "${task.title}" — bullets: 1) Hook 2) Problem 3) Solution 4) CTA`;
      state.factoryLogs.push(`Outline produced (free model) for task ${task.id}`);
      addXP(3);
      refreshUI();
      // Stage 2: platform-adapt (premium recommended)
      setTimeout(()=> {
        task.status = 'drafts_ready';
        task.drafts = task.platforms.map(p => ({platform:p, text: `Draft for ${p} of theme "${task.title}" — tailored tone.`}));
        state.factoryLogs.push(`Platform drafts generated (standard). Use premium for richer multimedia variants.`);
        refreshUI();
        notifyOrchestration(`task.${task.id}.drafts_ready`);
      }, 1400);
    }, 800);
  }

  // Task card button actions (delegate)
  taskFeed.addEventListener('click', (ev)=>{
    const btn = ev.target.closest('button');
    if (!btn) return;
    const id = btn.dataset.id;
    const action = btn.dataset.action;
    const task = state.tasks.find(t=>t.id===id);
    if (!task) return;
    if (action==='view') { alert(JSON.stringify(task, null, 2)); }
    if (action==='upgrade') {
      // attempt premium upgrade cost
      const cost = 4; // cents ~ $0.04
      const premiumCost = 40; // cents = $0.40 per heavy request simulation
      if (!confirm('Upgrade to premium for richer drafts? Cost: $0.04 per heavy call. Proceed?')) return;
      if (!spendBudget(cost)) { alert('Budget too low.'); return; }
      // simulate premium re-generation
      setTimeout(()=>{
        task.drafts = task.platforms.map(p => ({platform:p, text: `✨ Premium ${p} draft with richer tone, hooks and CTA for "${task.title}"`}));
        task.status = 'premium_ready';
        state.factoryLogs.push(`Premium drafts generated for task ${task.id} using premium model.`);
        addXP(6);
        refreshUI();
        confettiBurst(15);
      }, 900);
    }
  });

  // Factory flows
  btnCreateAgentDef.addEventListener('click', ()=>{
    const name = newAgentName.value.trim() || `agent-${Math.random().toString(36).slice(2,6)}`;
    state.factoryLogs.push(`Agent "${name}" proposed by DomainOnboard.`);
    state.factoryLogs.push(`Event: propose -> Vision review queued.`);
    addXP(8);
    refreshUI();
  });

  btnRunFactory.addEventListener('click', async ()=>{
    const prepareMsg = `Factory run started — orchestrating CoE agents`;
    state.factoryLogs.push(prepareMsg);
    refreshUI();
    // animate CoE nodes using GSAP
    gsap.fromTo('#coe-domain',{y:-6},{y:0,duration:0.6,repeat:3,yoyo:true});
    gsap.fromTo('#coe-vision',{y:-6,opacity:0.9},{y:0,duration:0.5,repeat:4,yoyo:true});
    // staged events
    await tick(600); state.factoryLogs.push('DomainOnboard produced role-template and market analysis');
    refreshUI(); await tick(900);
    // Vision review
    state.factoryLogs.push('Vision reviewing market fit & salary reports...');
    refreshUI(); await tick(1200);
    // Vision approves
    const approved = Math.random()>0.12;
    if (approved){
      state.factoryLogs.push('Vision: Approved ✅ — manifest attestation produced (ed25519 signature simulated).');
      state.factoryLogs.push('Triggering Test & Security agents...');
      refreshUI(); await tick(1200);
      state.factoryLogs.push('TestAgent: unit/integration tests passed.');
      await tick(800);
      state.factoryLogs.push('SecurityAgent: vulnerability scan passed.');
      await tick(700);
      state.factoryLogs.push('PackagingAgent: built container image and docs.');
      await tick(600);
      state.factoryLogs.push('Factory: Agent certified and ready for publish.');
      // publish to marketplace (simulate)
      const agentName = `social-media-agent-${Math.random().toString(36).slice(2,4)}`;
      state.publishedAgents.push(agentName);
      state.instances.push({name:`${agentName}-inst`, agent:agentName, status:'idle'});
      addXP(30);
      confettiBurst(30);
    } else {
      state.factoryLogs.push('Vision: Rejected. Reason: low market signal. Back to DomainOnboard.');
    }
    refreshUI();
  });

  // Incidents & escalation
  btnGenIncident.addEventListener('click', ()=>{
    const id = randId('inc');
    const incident = { id, title: 'Content generation failed', level: 'L1', status: 'open', createdAt:Date.now() };
    state.incidents.push(incident);
    state.factoryLogs.push('Incident created: Content generation failure');
    addXP(4);
    escalateIncident(incident);
    refreshUI();
  });

  function escalateIncident(incident){
    // L1 tries quick fix
    setTimeout(()=>{
      incident.status = 'triaged by L1';
      state.factoryLogs.push(`L1 triage performed on ${incident.id}`);
      refreshUI();
      // escalate to L2 if unresolved
      setTimeout(()=>{
        incident.level = 'L2';
        incident.status = 'escalated to L2';
        state.factoryLogs.push(`Escalated to L2 for root cause analysis`);
        refreshUI();
        // L2 applies patch
        setTimeout(()=>{
          incident.level = 'L3';
          incident.status = 'escalated to L3 - infra';
          state.factoryLogs.push(`Escalated to L3 - infra team investigating`);
          refreshUI();
          setTimeout(()=>{
            incident.status = 'resolved';
            incident.resolvedAt = Date.now();
            state.factoryLogs.push(`Incident ${incident.id} resolved by L3`);
            addXP(12);
            refreshUI();
            confettiBurst(8);
          }, 1600);
        }, 1200);
      }, 1000);
    }, 800);
  }

  // Orchestra notifications
  function notifyOrchestration(msg){
    state.orchestraLog = state.orchestraLog || [];
    const stamp = new Date().toLocaleTimeString();
    state.orchestraLog.push(`${stamp} — ${msg}`);
    refreshUI();
  }

  // reset & export
  btnReset.addEventListener('click', ()=>{
    if (!confirm('Reset sandbox to default state?')) return;
    localStorage.removeItem(STORAGE_KEY);
    state = structuredClone(DEFAULT);
    refreshUI();
  });

  btnExport.addEventListener('click', ()=>{
    const dataStr = JSON.stringify(state, null, 2);
    const blob = new Blob([dataStr], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'waooaw_sandbox_state.json'; a.click();
    URL.revokeObjectURL(url);
  });

  // small helpers
  function tick(ms){ return new Promise(r => setTimeout(r, ms)); }
  function confettiBurst(p = 60){
    confetti({
      particleCount: p,
      spread: 70,
      origin: { y: 0.3 }
    });
  }

  // initial gentle animation
  gsap.fromTo('.panel',{y:12,opacity:0},{y:0,opacity:1,duration:0.9,stagger:0.06,ease:'power3.out'});

  // unveil last usage hint
  if (!state.factoryLogs.length) {
    state.factoryLogs.push('Welcome to WAOOAW sandbox. Try starting a trial, proposing an agent, and running the factory!');
    addXP(12);
    refreshUI();
  }

})();
