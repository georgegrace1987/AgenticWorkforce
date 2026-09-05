const fileInput = document.querySelector('#file-input');
const fileList = document.querySelector('#file-list');
const chatForm = document.querySelector('#chat-form');
const messageInput = document.querySelector('#message-input');
const messages = document.querySelector('#messages');
const readinessScore = document.querySelector('#readiness-score');
const readinessProgress = document.querySelector('#readiness-progress');
const readinessCopy = document.querySelector('#readiness-copy');
const generateButton = document.querySelector('#generate-button');
const requirementsSummary = document.querySelector('#requirements-summary');
const sessionButton = document.querySelector('.session-button');
const stopQuestionsButton = document.querySelector('#stop-questions-button');
const supportedExtensions = new Set(['.docx', '.pptx', '.xlsx', '.csv', '.txt']);
const sessionId = localStorage.getItem('requirements-session-id') || crypto.randomUUID();
localStorage.setItem('requirements-session-id', sessionId);

sessionButton.addEventListener('click', () => {
  localStorage.removeItem('requirements-session-id');
  window.location.reload();
});

fileInput.addEventListener('change', async () => {
  const files = [...fileInput.files];
  fileList.innerHTML = files.length
    ? files.map((file) => `<p class="file-item">${file.name}</p>`).join('')
    : '<p class="muted">No files attached yet.</p>';
  if (!files.length) return;
  const file = files[0];
  const extension = `.${file.name.split('.').pop().toLowerCase()}`;
  if (!supportedExtensions.has(extension)) {
    appendMessage('!', 'System', 'Please attach a DOCX, PPTX, XLSX, CSV, or TXT file so I can extract its requirements.');
    return;
  }
  fileList.insertAdjacentHTML('beforeend', '<p class="muted">Reading document...</p>');
  try {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('file', file);
    const response = await fetch('/api/documents', { method: 'POST', body: formData });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(formatErrorDetail(detail.detail) || `Upload failed (${response.status})`);
    }
    const result = await response.json();
    appendMessage('W', 'Wizard', `I read ${file.name} and captured the document requirements. ${result.assistant_message}`);
    updateReadiness(result);
    fileList.lastElementChild.textContent = 'Document analyzed.';
  } catch (error) {
    appendMessage('!', 'System', `I could not read the document. ${error.message}`);
    fileList.lastElementChild.textContent = 'Document could not be analyzed.';
  }
});

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  appendMessage('Y', 'You', text);
  messageInput.value = '';
  const sendButton = chatForm.querySelector('.send-button');
  sendButton.disabled = true;
  sendButton.textContent = 'Thinking...';
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    const result = await response.json();
    appendMessage('W', 'Wizard', result.assistant_message);
    updateReadiness(result);
  } catch (error) {
    appendMessage('!', 'System', `I could not reach the requirements engine. ${error.message}`);
  } finally {
    sendButton.disabled = false;
    sendButton.innerHTML = 'Send <span aria-hidden="true">→</span>';
  }
  messageInput.focus();
});

stopQuestionsButton.addEventListener('click', async () => {
  messageInput.value = 'Stop asking questions';
  chatForm.requestSubmit();
});

function appendMessage(initial, author, text) {
  const message = document.createElement('article');
  message.className = 'message';
  const safeText = text.replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('\n', '<br>');
  message.innerHTML = `<div class="avatar">${initial}</div><div><p class="message-meta">${author} <time>Now</time></p><p>${safeText}</p></div>`;
  messages.append(message);
  message.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatErrorDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('; ');
  }
  if (detail && typeof detail === 'object') return detail.message || JSON.stringify(detail);
  return '';
}

function updateReadiness(result) {
  renderRequirements(result.requirements);
  readinessScore.textContent = `${result.readiness_score}%`;
  readinessProgress.style.width = `${result.readiness_score}%`;
  const questionsPaused = result.requirements?.questions_paused || false;
  readinessCopy.textContent = result.open_questions.length
    ? `Next decision to refine: ${result.open_questions[0]}`
    : questionsPaused
    ? 'Questions are paused. You can review and generate the SRD now.'
    : 'The brief has a strong starting shape. Review it before generating the SRD.';
  const canGenerate = (result.readiness_score === 100 && result.open_questions.length === 0) || questionsPaused;
  generateButton.disabled = !canGenerate;
  document.querySelectorAll('[data-readiness-key]').forEach((item) => {
    const complete = result.readiness_items?.[item.dataset.readinessKey] || false;
    item.classList.toggle('complete', complete);
    item.querySelector('span').textContent = complete ? '✓' : '○';
  });
}

function renderRequirements(requirements) {
  const sections = [
    ['Business objective', requirements.business_objective ? [requirements.business_objective] : []],
    ['Stakeholders', requirements.stakeholders],
    ['User roles', requirements.user_roles],
    ['Functional requirements', requirements.functional_requirements],
    ['Non-functional requirements', requirements.non_functional_requirements],
    ['Constraints', requirements.constraints],
    ['Risks', requirements.risks],
    ['Assumptions', requirements.assumptions],
    ['Open questions', requirements.open_questions],
  ];
  requirementsSummary.innerHTML = sections.map(([label, values]) => {
    const items = values.length
      ? `<ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join('')}</ul>`
      : '<p class="muted">None captured yet.</p>';
    return `<div class="summary-group"><strong>${label}</strong>${items}</div>`;
  }).join('');
}

function escapeHtml(value) {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

generateButton.addEventListener('click', async () => {
  generateButton.disabled = true;
  generateButton.textContent = 'Preparing...';
  try {
    const response = await fetch('/api/srd/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!response.ok) throw new Error(`Generation failed (${response.status})`);
    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'software-requirements-document.docx';
    link.click();
    URL.revokeObjectURL(downloadUrl);
    readinessCopy.textContent = 'Your SRD is ready and has been downloaded.';
  } catch (error) {
    readinessCopy.textContent = error.message;
  } finally {
    generateButton.disabled = false;
    generateButton.innerHTML = 'Generate SRD <span aria-hidden="true">↗</span>';
  }
});

messageInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
