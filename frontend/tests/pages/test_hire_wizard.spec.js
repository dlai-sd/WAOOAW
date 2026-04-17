import { goToStep, showError, submitStep1, submitStep2, submitStep3, wizardState }
  from '../../pages/hire.js';

beforeEach(() => {
  document.body.innerHTML = `
    <div id="wizard-step-1" class="wizard-step">
      <input id="nickname" value="">
      <p id="nickname-error" hidden></p>
      <p id="step1-error" hidden></p>
    </div>
    <div id="wizard-step-2" class="wizard-step" hidden>
      <form id="skill-config-form">
        <input name="brand_name" value="TestBrand">
      </form>
      <p id="step2-error" hidden></p>
    </div>
    <div id="wizard-step-3" class="wizard-step" hidden>
      <select id="schedule"><option value="daily">Daily</option></select>
      <input id="approval-toggle" type="checkbox" checked>
      <p id="step3-error" hidden></p>
    </div>
    <div id="step-ind-1" class="step-indicator"></div>
    <div id="step-ind-2" class="step-indicator"></div>
    <div id="step-ind-3" class="step-indicator"></div>
  `;
  wizardState.step = 1;
  wizardState.agentId = null;
  wizardState.hiredInstanceId = null;
  goToStep(1);
});

describe('hire wizard', () => {
  test('T1: empty nickname shows error and stays on step 1', async () => {
    document.getElementById('nickname').value = '';
    await submitStep1();
    expect(document.getElementById('nickname-error').hidden).toBe(false);
    expect(document.getElementById('nickname-error').textContent).toBe('Nickname is required');
    expect(document.getElementById('wizard-step-2').hidden).toBe(true);
  });

  test('T2: successful POST /cp/hired-agents advances to step 2', async () => {
    document.getElementById('nickname').value = 'My Agent';
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'hired-123' }) });
    await submitStep1();
    expect(document.getElementById('wizard-step-1').hidden).toBe(true);
    expect(document.getElementById('wizard-step-2').hidden).toBe(false);
  });

  test('T3: PATCH /cp/skill-configs returns 500 shows inline error, does not advance', async () => {
    wizardState.hiredInstanceId = 'hired-123';
    goToStep(2);
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({ detail: 'Internal error' }) });
    await submitStep2();
    expect(document.getElementById('step2-error').hidden).toBe(false);
    expect(document.getElementById('wizard-step-3').hidden).toBe(true);
  });

  test('T4: happy path completes and redirects to /my-agents', async () => {
    const origLocation = window.location;
    delete window.location;
    window.location = { href: '' };

    document.getElementById('nickname').value = 'My Agent';
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'hired-123' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    await submitStep1();
    await submitStep2();
    await submitStep3();

    expect(window.location.href).toBe('/my-agents');
    window.location = origLocation;
  });
});
