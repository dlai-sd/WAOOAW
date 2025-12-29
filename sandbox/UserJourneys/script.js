// Improved mission selection and playback handlers for Sandbox User Journeys
// Features:
// - Proper wiring of mission buttons
// - Play, Step, Abort handlers
// - Timeline rendering for selected mission with current step highlighting
// - Dispatches a CustomEvent 'mission-step' with detail { missionId, stepIndex, step }
// - Graceful handling when mission data isn't available in DOM: will look for window.missions or window.MISSION_DATA

(function () {
  'use strict';

  // Configuration
  var STEP_INTERVAL_MS = 1000; // default play interval

  // State
  var selectedMissionId = null;
  var selectedMission = null;
  var currentStepIndex = -1; // -1 means not started
  var isPlaying = false;
  var playTimer = null;

  // DOM refs (lazy-resolved)
  var missionButtons = null;
  var playBtn = null;
  var stepBtn = null;
  var abortBtn = null;
  var timelineContainer = null;

  // Utility: Try to find mission data by id
  function getMissionById(id) {
    if (!id) return null;
    // If missions are stored on window as an object or array
    if (window.missions) {
      if (Array.isArray(window.missions)) {
        return window.missions.find(function (m) { return String(m.id) === String(id); }) || null;
      }
      if (typeof window.missions === 'object') {
        return window.missions[id] || null;
      }
    }
    if (window.MISSION_DATA) {
      var md = window.MISSION_DATA;
      if (Array.isArray(md)) {
        return md.find(function (m) { return String(m.id) === String(id); }) || null;
      }
      return md[id] || null;
    }
    // Try to find inline JSON on the button
    var btn = document.querySelector('.mission-btn[data-mission-id="' + id + '"]') || document.querySelector('.mission-btn[data-mission="' + id + '"]');
    if (btn) {
      var raw = btn.dataset.mission || btn.getAttribute('data-mission-json');
      if (raw) {
        try {
          return JSON.parse(raw);
        } catch (e) {
          // not JSON, maybe the id is enough
        }
      }
    }
    return null;
  }

  // Render timeline for mission
  function renderTimeline(mission) {
    if (!timelineContainer) return;
    timelineContainer.innerHTML = '';
    if (!mission || !Array.isArray(mission.steps) || mission.steps.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'timeline-empty';
      empty.textContent = 'No steps available for this mission.';
      timelineContainer.appendChild(empty);
      return;
    }

    var list = document.createElement('ol');
    list.className = 'timeline-list';

    mission.steps.forEach(function (step, idx) {
      var li = document.createElement('li');
      li.className = 'timeline-step';
      li.dataset.stepIndex = idx;

      var title = document.createElement('div');
      title.className = 'timeline-step-title';
      title.textContent = step.title || ('Step ' + (idx + 1));

      var details = document.createElement('div');
      details.className = 'timeline-step-details';
      details.textContent = step.description || (step.action ? JSON.stringify(step.action) : '');

      li.appendChild(title);
      li.appendChild(details);

      list.appendChild(li);
    });

    timelineContainer.appendChild(list);

    // Highlight current step if any
    highlightStep(currentStepIndex);
  }

  function clearTimelineSelection() {
    if (!timelineContainer) return;
    var selected = timelineContainer.querySelectorAll('.timeline-step.current');
    selected.forEach(function (el) { el.classList.remove('current'); });
  }

  function highlightStep(index) {
    clearTimelineSelection();
    if (!timelineContainer) return;
    if (index == null || index < 0) return;
    var node = timelineContainer.querySelector('.timeline-step[data-step-index="' + index + '"]');
    if (node) {
      node.classList.add('current');
      // scroll into view smoothly if supported
      if (node.scrollIntoView) {
        try { node.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) { node.scrollIntoView(); }
      }
    }
  }

  function executeStep(mission, index) {
    if (!mission || !Array.isArray(mission.steps)) return;
    var step = mission.steps[index];
    if (!step) return;

    // Primary integration point: fire a CustomEvent so host app can run the step
    var evDetail = { missionId: mission.id, stepIndex: index, step: step };
    var ev = new CustomEvent('mission-step', { detail: evDetail });
    window.dispatchEvent(ev);

    // Fallback console logging
    console.log('Executing mission step', evDetail);
  }

  function stepNext() {
    if (!selectedMission) {
      console.warn('No mission selected; step ignored.');
      return;
    }
    var total = Array.isArray(selectedMission.steps) ? selectedMission.steps.length : 0;
    if (currentStepIndex < total - 1) {
      currentStepIndex++;
      highlightStep(currentStepIndex);
      executeStep(selectedMission, currentStepIndex);

      // If last step reached, stop playing
      if (currentStepIndex >= total - 1) {
        stopPlaying();
        // dispatch completion event
        var doneEv = new CustomEvent('mission-complete', { detail: { missionId: selectedMission.id } });
        window.dispatchEvent(doneEv);
        console.log('Mission complete', selectedMission.id);
      }
    } else {
      // Already at end
      stopPlaying();
    }
  }

  function startPlaying() {
    if (isPlaying) return;
    if (!selectedMission) {
      alert('Please select a mission to play.');
      return;
    }
    isPlaying = true;
    playBtn && playBtn.classList.add('playing');
    // If not started, start from next step
    if (currentStepIndex < 0) currentStepIndex = -1;

    playTimer = setInterval(function () {
      stepNext();
    }, STEP_INTERVAL_MS);
  }

  function stopPlaying() {
    isPlaying = false;
    playBtn && playBtn.classList.remove('playing');
    if (playTimer) {
      clearInterval(playTimer);
      playTimer = null;
    }
  }

  function handlePlayClick(e) {
    e && e.preventDefault && e.preventDefault();
    if (isPlaying) {
      stopPlaying();
      return;
    }
    startPlaying();
  }

  function handleStepClick(e) {
    e && e.preventDefault && e.preventDefault();
    // If playing, step button should pause and step once
    if (isPlaying) {
      stopPlaying();
    }
    stepNext();
  }

  function handleAbortClick(e) {
    e && e.preventDefault && e.preventDefault();
    // Stop playing and reset state
    stopPlaying();
    currentStepIndex = -1;
    highlightStep(currentStepIndex);

    // Dispatch abort event
    if (selectedMission) {
      var abortEv = new CustomEvent('mission-abort', { detail: { missionId: selectedMission.id } });
      window.dispatchEvent(abortEv);
    }
    console.log('Playback aborted');
  }

  function onMissionButtonClick(evt) {
    var btn = evt.currentTarget;
    var id = btn.dataset.missionId || btn.dataset.mission || btn.getAttribute('data-mission-id') || btn.getAttribute('data-mission');

    if (!id) {
      // Try to parse JSON from data-mission
      var raw = btn.dataset.mission || btn.getAttribute('data-mission-json');
      if (raw) {
        try {
          var parsed = JSON.parse(raw);
          if (parsed && parsed.id !== undefined) {
            id = parsed.id;
            // also store parsed mission directly on button for quick access
            btn.__missionObj = parsed;
          }
        } catch (e) {
          // ignore
        }
      }
    }

    // Select the mission
    selectMission(id, btn);
  }

  function clearMissionButtonSelection() {
    if (!missionButtons) return;
    missionButtons.forEach(function (b) { b.classList.remove('selected'); });
  }

  function selectMission(id, btnEl) {
    // If a button passed has an inline mission object, use that first
    if (btnEl && btnEl.__missionObj) {
      selectedMission = btnEl.__missionObj;
      selectedMissionId = selectedMission.id;
    } else {
      // look up mission data
      selectedMission = getMissionById(id);
      selectedMissionId = id;
    }

    clearMissionButtonSelection();
    if (btnEl) btnEl.classList.add('selected');

    // Reset playback state for new mission selection
    stopPlaying();
    currentStepIndex = -1;

    // Render timeline for selected mission
    renderTimeline(selectedMission);

    // Dispatch mission-selected event
    var ev = new CustomEvent('mission-selected', { detail: { missionId: selectedMissionId, mission: selectedMission } });
    window.dispatchEvent(ev);

    console.log('Mission selected', selectedMissionId, selectedMission);
  }

  function setupElements() {
    missionButtons = Array.prototype.slice.call(document.querySelectorAll('.mission-btn')) || [];
    playBtn = document.querySelector('.mission-play');
    stepBtn = document.querySelector('.mission-step');
    abortBtn = document.querySelector('.mission-abort');
    timelineContainer = document.querySelector('.mission-timeline');

    // attach mission button handlers
    if (missionButtons && missionButtons.length) {
      missionButtons.forEach(function (btn) {
        btn.removeEventListener('click', onMissionButtonClick);
        btn.addEventListener('click', onMissionButtonClick);
      });
    }

    if (playBtn) {
      playBtn.removeEventListener('click', handlePlayClick);
      playBtn.addEventListener('click', handlePlayClick);
    }
    if (stepBtn) {
      stepBtn.removeEventListener('click', handleStepClick);
      stepBtn.addEventListener('click', handleStepClick);
    }
    if (abortBtn) {
      abortBtn.removeEventListener('click', handleAbortClick);
      abortBtn.addEventListener('click', handleAbortClick);
    }

    // keyboard shortcuts: Space = play/pause, ArrowRight = step, Escape = abort
    window.addEventListener('keydown', function (e) {
      // avoid interfering with input fields
      var active = document.activeElement;
      if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)) return;
      if (e.code === 'Space') {
        e.preventDefault();
        handlePlayClick();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        handleStepClick();
      } else if (e.code === 'Escape') {
        e.preventDefault();
        handleAbortClick();
      }
    });
  }

  // Public API for other scripts to control playback programmatically
  window.UserJourneyPlayback = {
    selectMissionById: function (id) { selectMission(id, document.querySelector('.mission-btn[data-mission-id="' + id + '"]') || document.querySelector('.mission-btn[data-mission="' + id + '"]')); },
    play: function () { startPlaying(); },
    stop: function () { stopPlaying(); },
    step: function () { stepNext(); },
    abort: function () { handleAbortClick(); },
    getState: function () { return { missionId: selectedMissionId, isPlaying: isPlaying, currentStepIndex: currentStepIndex }; }
  };

  // Initialize on DOM ready
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(setupElements, 0);
  } else {
    document.addEventListener('DOMContentLoaded', setupElements);
  }

})();
