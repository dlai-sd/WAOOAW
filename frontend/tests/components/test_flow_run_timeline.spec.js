import { renderFlowRunTimeline } from '../../components/FlowRunTimeline.js';

const MOCK_FR = { id: 'fr-1', status: 'running' };
const MOCK_CRS = [
  { step_name: 'GoalConfigPump',   status: 'completed', duration_ms: 120 },
  { step_name: 'ContentProcessor', status: 'running',   duration_ms: null },
  { step_name: 'LinkedInPublisher',status: 'pending',   duration_ms: null },
];

describe('renderFlowRunTimeline', () => {
  test('T1: running flow with 3 steps renders 3 step nodes; running step has --pulse class', () => {
    const div = document.createElement('div');
    div.innerHTML = renderFlowRunTimeline(MOCK_FR, MOCK_CRS);
    expect(div.querySelectorAll('.timeline-step').length).toBe(3);
    const runningStep = div.querySelector('.timeline-step--running');
    expect(runningStep).not.toBeNull();
    expect(runningStep.classList.contains('timeline-step--pulse')).toBe(true);
  });

  test('T2: flowRun=null renders empty-state paragraph', () => {
    const div = document.createElement('div');
    div.innerHTML = renderFlowRunTimeline(null, []);
    expect(div.querySelector('.empty-state')).not.toBeNull();
    expect(div.textContent).toContain('No runs yet');
  });
});
