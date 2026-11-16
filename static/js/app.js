const api = {
  async request(path, options = {}) {
    const response = await fetch(path, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });

    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw new Error(data.detail || data.message || 'Request failed');
    }

    return data;
  },
};

const state = {
  token: localStorage.getItem('neon_token') || '',
};

const els = {
  loginPanel: document.getElementById('loginPanel'),
  memberView: document.getElementById('memberView'),
  emailInput: document.getElementById('emailInput'),
  passwordInput: document.getElementById('passwordInput'),
  loginStatus: document.getElementById('loginStatus'),
  loginBtn: document.getElementById('loginBtn'),
  logoutBtn: document.getElementById('logoutBtn'),
  totalBalance: document.getElementById('totalBalance'),
  availableBalance: document.getElementById('availableBalance'),
  cardCount: document.getElementById('cardCount'),
  accountsList: document.getElementById('accountsList'),
  paymentForm: document.getElementById('paymentForm'),
  paymentStatus: document.getElementById('paymentStatus'),
  historyList: document.getElementById('historyList'),
  fraudSummary: document.getElementById('fraudSummary'),
  fraudAlerts: document.getElementById('fraudAlerts'),
};

const money = (cents) => `$${(cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

async function login() {
  const email = els.emailInput.value.trim();
  const password = els.passwordInput.value;

  try {
    const result = await api.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    state.token = result.access_token;
    localStorage.setItem('neon_token', state.token);
    els.loginStatus.textContent = 'Signed in';
    loadDashboard();
  } catch (error) {
    els.loginStatus.textContent = error.message;
  }
}

function logout() {
  state.token = '';
  localStorage.removeItem('neon_token');
  els.memberView.hidden = true;
  els.loginPanel.hidden = false;
}

async function loadDashboard() {
  if (!state.token) return;

  els.loginPanel.hidden = true;
  els.memberView.hidden = false;

  try {
    const [accounts, cards, history, fraud] = await Promise.all([
      api.request('/api/accounts', { headers: { Authorization: `Bearer ${state.token}` } }),
      api.request('/api/cards', { headers: { Authorization: `Bearer ${state.token}` } }),
      api.request('/api/payments/history', { headers: { Authorization: `Bearer ${state.token}` } }),
      api.request('/api/fraud/posture', { headers: { Authorization: `Bearer ${state.token}` } }),
    ]);

    const total = accounts.reduce((sum, account) => sum + Number(account.balance_cents || 0), 0);
    els.totalBalance.textContent = money(total);
    els.availableBalance.textContent = money(total);
    els.cardCount.textContent = cards.length;

    els.accountsList.innerHTML = accounts.map((account) => `
      <div class="account-item">
        <small>${account.account_type.toUpperCase()}</small>
        <strong>${account.name}</strong>
        <div>${account.account_number}</div>
        <small>${money(account.balance_cents)}</small>
      </div>
    `).join('');

    els.historyList.innerHTML = history.slice(0, 6).map((item) => `
      <li><strong>${item.merchant}</strong><div>${item.status} · ${money(item.amount_cents)}</div></li>
    `).join('');

    els.fraudSummary.innerHTML = `Score: ${fraud.score} / 100 · Status: ${fraud.status}`;
    els.fraudAlerts.innerHTML = '<li>No recent fraud anomalies detected.</li>';
  } catch (error) {
    els.loginStatus.textContent = error.message;
  }
}

els.loginBtn.addEventListener('click', login);
els.logoutBtn.addEventListener('click', logout);

els.paymentForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.token) return;

  try {
    const merchant = document.getElementById('merchantInput').value || 'Test Merchant';
    const amount = Number(document.getElementById('amountInput').value || 0);
    const pan = document.getElementById('panInput').value || '4111111111111111';
    const result = await api.request('/api/payments/authorize', {
      method: 'POST',
      headers: { Authorization: `Bearer ${state.token}` },
      body: JSON.stringify({ merchant, amount_cents: amount, pan, idempotency_key: `demo-${Date.now()}` }),
    });
    els.paymentStatus.textContent = `Authorization ${result.status} · ${money(result.amount_cents)}`;
    loadDashboard();
  } catch (error) {
    els.paymentStatus.textContent = error.message;
  }
});

if (state.token) {
  loadDashboard();
}
