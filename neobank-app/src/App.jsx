import { useMemo, useState } from 'react';

const initialAccounts = [
  { id: 'checking', name: 'Everyday checking', type: 'Checking ·· 4821', balance: 8420.54, number: '•••• 4821', color: 'blue' },
  { id: 'savings', name: 'Rainy day savings', type: 'Savings ·· 1906', balance: 12480.2, number: '•••• 1906', color: 'mint' },
];

const initialTransactions = [
  { id: 1, merchant: 'Harbor Coffee', category: 'Food & drink', date: 'Today, 9:41 AM', amount: -6.8, status: 'Completed', icon: '☕' },
  { id: 2, merchant: 'Payroll deposit', category: 'Income', date: 'Today, 8:02 AM', amount: 2450, status: 'Completed', icon: '↙' },
  { id: 3, merchant: 'Metro Transit', category: 'Transport', date: 'Yesterday', amount: -14.5, status: 'Completed', icon: '↗' },
  { id: 4, merchant: 'Grove Market', category: 'Groceries', date: 'Yesterday', amount: -82.17, status: 'Completed', icon: '⌂' },
  { id: 5, merchant: 'Streaming Plus', category: 'Subscriptions', date: 'Nov 12, 2026', amount: -12.99, status: 'Pending', icon: '▶' },
];

const nav = [
  ['Overview', '⌂'], ['Accounts', '▤'], ['Cards', '▰'], ['Payments', '↗'], ['Activity', '↕'], ['Settings', '⚙'],
];
const money = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

function Icon({ children }) { return <span className="nav-icon" aria-hidden="true">{children}</span>; }

function App() {
  const [page, setPage] = useState('Overview');
  const [accounts, setAccounts] = useState(initialAccounts);
  const [transactions, setTransactions] = useState(initialTransactions);
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState('');
  const [mobileNav, setMobileNav] = useState(false);
  const [form, setForm] = useState({ from: 'checking', to: 'savings', amount: '' });
  const [cardLocked, setCardLocked] = useState(false);
  const [search, setSearch] = useState('');
  const total = useMemo(() => accounts.reduce((sum, account) => sum + account.balance, 0), [accounts]);
  const filteredTransactions = transactions.filter((item) => `${item.merchant} ${item.category}`.toLowerCase().includes(search.toLowerCase()));

  function notify(message) {
    setToast(message);
    window.setTimeout(() => setToast(''), 2800);
  }

  function changePage(next) {
    setPage(next);
    setMobileNav(false);
  }

  function submitTransfer(event) {
    event.preventDefault();
    const amount = Number(form.amount);
    const from = accounts.find((account) => account.id === form.from);
    const to = accounts.find((account) => account.id === form.to);
    if (!amount || amount <= 0 || !from || !to || from.id === to.id) {
      notify('Choose two different accounts and enter a valid amount.');
      return;
    }
    if (amount > from.balance) {
      notify('This demo account does not have enough available funds.');
      return;
    }
    setAccounts((current) => current.map((account) => account.id === from.id ? { ...account, balance: account.balance - amount } : account.id === to.id ? { ...account, balance: account.balance + amount } : account));
    setTransactions((current) => [{ id: Date.now(), merchant: `Transfer to ${to.name}`, category: 'Account transfer', date: 'Just now', amount: -amount, status: 'Completed', icon: '↗' }, ...current]);
    setModal(false);
    setForm({ ...form, amount: '' });
    notify('Demo transfer completed locally. No funds moved.');
  }

  return (
    <div className="app-shell">
      <div className="demo-banner" role="status" aria-live="polite">
        <span className="demo-pill">DEMO MODE</span>
        <span>Fictional banking prototype — no real accounts, funds, or payment rails are connected.</span>
      </div>
      {mobileNav && <button className="scrim" aria-label="Close navigation" onClick={() => setMobileNav(false)} />}
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <a className="brand" href="#home" onClick={(event) => { event.preventDefault(); changePage('Overview'); }}>
          <span className="brand-mark">N</span><span><b>neon</b><small>MEMBER BANKING</small></span>
        </a>
        <div className="member-label">YOUR MONEY</div>
        <nav className="nav-list" aria-label="Main navigation">
          {nav.map(([label, icon]) => <button key={label} className={`nav-item ${page === label ? 'active' : ''}`} onClick={() => changePage(label)}><Icon>{icon}</Icon>{label}{label === 'Activity' && <span className="nav-count">5</span>}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="help-card"><span className="help-spark">✦</span><b>Here when you need us</b><small>Talk to a real person, any time.</small><button onClick={() => notify('Support is a demo placeholder.')}>Get support <span>↗</span></button></div>
          <button className="profile"><span className="avatar">SC</span><span className="profile-name"><b>Sophie Cunningham</b><small>Everyday member</small></span><span className="dots">···</span></button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileNav(true)}>☰</button>
          <div className="crumb">Member portal <span>/</span> <b>{page}</b></div>
          <div className="top-actions"><span className="secure"><i /> Secure session</span><button className="bell" aria-label="Notifications" onClick={() => notify('You’re all caught up.')}>♧<i /></button><span className="top-avatar">SC</span></div>
        </header>

        <div className="page-wrap">
          <div className="welcome-row"><div><div className="eyebrow">MONDAY, NOVEMBER 16, 2026</div><h1>{page === 'Overview' ? <>Good morning, Sophie <span className="wave">✦</span></> : page}</h1><p>{page === 'Overview' ? 'Here’s what’s happening with your money today.' : page === 'Payments' ? 'Move money between your demo accounts.' : `Your Neon ${page.toLowerCase()} at a glance.`}</p></div><button className="button button-primary" onClick={() => setModal(true)}><span>＋</span> Make a transfer</button></div>

          {page === 'Overview' && <>
            <section className="balance-panel">
              <div className="balance-copy"><div className="balance-label">TOTAL ACCOUNT BALANCE <button className="eye" aria-label="Toggle balance visibility" onClick={(event) => { const el = document.getElementById('total-balance'); el.dataset.hidden = el.dataset.hidden === 'true' ? 'false' : 'true'; el.textContent = el.dataset.hidden === 'true' ? '••••••••' : money(total); }}>◎</button></div><div className="big-balance" id="total-balance">{money(total)}</div><div className="balance-change"><span>↗ 4.8%</span> <small>compared to last month</small></div></div>
              <div className="balance-chart" aria-label="Illustrative balance trend"><div className="chart-caption"><span>Balance trend</span><b>Last 7 days⌄</b></div><svg viewBox="0 0 360 100" role="img" aria-label="Upward balance trend chart"><defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#b7f2d3" stopOpacity=".3"/><stop offset="1" stopColor="#b7f2d3" stopOpacity="0"/></linearGradient></defs><path d="M0 74 C22 69 29 82 48 68 S78 70 95 56 S123 67 142 47 S174 61 193 39 S222 51 241 33 S269 42 286 26 S325 35 360 9 V100 H0Z" fill="url(#fill)"/><path d="M0 74 C22 69 29 82 48 68 S78 70 95 56 S123 67 142 47 S174 61 193 39 S222 51 241 33 S269 42 286 26 S325 35 360 9" fill="none" stroke="#b7f2d3" strokeWidth="3" strokeLinecap="round"/></svg><div className="chart-days"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div></div>
            </section>

            <div className="section-heading"><div><h2>Your accounts</h2><p>Two accounts, one clear view.</p></div><button className="text-button" onClick={() => changePage('Accounts')}>All accounts <span>→</span></button></div>
            <section className="account-grid">{accounts.map((account) => <article className={`account-card ${account.color}`} key={account.id}><div className="account-card-top"><span className="account-symbol">{account.id === 'checking' ? '◈' : '✳'}</span><span className="account-menu">···</span></div><div className="account-type">{account.type}</div><h3>{account.name}</h3><div className="account-balance">{money(account.balance)}</div><div className="account-foot"><span>•••• {account.number.slice(-4)}</span><span className="account-link" onClick={() => changePage('Accounts')}>Details ↗</span></div></article>)}</section>

            <div className="section-heading activity-heading"><div><h2>Recent activity</h2><p>Your latest account activity.</p></div><button className="text-button" onClick={() => changePage('Activity')}>View all <span>→</span></button></div>
            <TransactionList items={transactions.slice(0, 4)} />
            <div className="bottom-grid"><section className="insight-card"><div className="insight-icon">✦</div><div><b>A little progress adds up.</b><p>You’ve saved $320 this month. Keep going — you’re building great habits.</p></div><button onClick={() => changePage('Accounts')}>See savings →</button></section><section className="trust-card"><span className="shield">✓</span><div><b>Your money, protected</b><p>Security checkup complete · 2-step verification on</p></div><span className="trust-status">All good</span></section></div>
          </>}

          {page === 'Accounts' && <section className="account-grid account-grid-full">{accounts.map((account) => <article className={`account-card ${account.color}`} key={account.id}><div className="account-card-top"><span className="account-symbol">{account.id === 'checking' ? '◈' : '✳'}</span><span className="account-menu">···</span></div><div className="account-type">{account.type}</div><h3>{account.name}</h3><div className="account-balance">{money(account.balance)}</div><div className="account-foot"><span>•••• {account.number.slice(-4)}</span><span className="account-link" onClick={() => notify(`${account.name}: sandbox account details`)}>Details ↗</span></div></article>)}</section>}

          {page === 'Cards' && <section className="cards-layout"><div className="payment-card"><div className="card-brand"><span className="brand-mark small-mark">N</span><b>neon</b><span className="visa">VISA</span></div><div className="chip">▦</div><div className="pan">•••• &nbsp;•••• &nbsp;•••• &nbsp;4821</div><div className="card-bottom"><span>SOPHIE CUNNINGHAM<small>CARDHOLDER</small></span><span>08/29<small>EXPIRES</small></span></div></div><div className="card card-controls"><div className="section-heading"><div><h2>Card controls</h2><p>Manage your demo debit card.</p></div></div><div className="control-row"><span><b>Card status</b><small>Temporarily lock new purchases</small></span><button className={`toggle ${cardLocked ? 'on' : ''}`} onClick={() => { setCardLocked(!cardLocked); notify(cardLocked ? 'Demo card unlocked.' : 'Demo card locked.'); }} aria-label="Toggle card lock"><i /></button></div><div className="control-row"><span><b>Online purchases</b><small>Allow online transactions</small></span><button className="toggle on" onClick={(event) => event.currentTarget.classList.toggle('on')} aria-label="Toggle online purchases"><i /></button></div><div className="control-row"><span><b>Travel notice</b><small>Tell us when you’re away</small></span><button className="text-button" onClick={() => notify('Travel notice is a demo feature.')}>Set up →</button></div><button className="button button-secondary full-button" onClick={() => notify('Replacement card request saved in demo.')}>Request a replacement card</button></div></section>}

          {page === 'Payments' && <section className="payments-layout"><div className="card transfer-card"><h2>Move money</h2><p>Transfer between your Neon demo accounts instantly.</p><form onSubmit={submitTransfer}><label>From<select value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}>{accounts.map((a) => <option value={a.id} key={a.id}>{a.name} · {money(a.balance)}</option>)}</select></label><button className="swap-button" type="button" onClick={() => setForm({ ...form, from: form.to, to: form.from })}>↕</button><label>To<select value={form.to} onChange={(e) => setForm({ ...form, to: e.target.value })}>{accounts.map((a) => <option value={a.id} key={a.id}>{a.name} · {money(a.balance)}</option>)}</select></label><label>Amount<div className="amount-field"><span>$</span><input type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required /></div></label><div className="transfer-note"><span>⚡</span> Usually arrives instantly <b>No fee</b></div><button className="button button-primary full-button" type="submit">Review transfer →</button></form></div><div className="card side-note"><span className="note-icon">✦</span><h3>Simple, secure transfers</h3><p>This demo lets you move sample balances between your checking and savings accounts. It does not connect to a bank or move real money.</p><div className="mini-line"><span>Transfer limit</span><b>$5,000 / day</b></div><div className="mini-line"><span>Delivery</span><b>Instant (demo)</b></div></div></section>}

          {page === 'Activity' && <section className="card activity-page"><div className="activity-toolbar"><div><h2>All activity</h2><p>Review your recent transactions.</p></div><input className="search" type="search" placeholder="Search activity" value={search} onChange={(e) => setSearch(e.target.value)} /></div><TransactionList items={filteredTransactions} /></section>}

          {page === 'Settings' && <section className="card settings-card"><h2>Settings & preferences</h2><p>Manage your demo profile and account preferences.</p>{[['Personal information', 'Sophie Cunningham · sophie@example.test'], ['Sign-in & security', 'Two-step verification is on'], ['Notifications', 'Email and push alerts enabled'], ['Privacy', 'Review data and privacy choices']].map(([title, detail]) => <button className="setting-row" key={title} onClick={() => notify(`${title} is a demo placeholder.`)}><span><b>{title}</b><small>{detail}</small></span><span>→</span></button>)}</section>}

          <footer className="footer-note"><span>◉</span> Neon Bank is a fictional demo. No real accounts, cards, or financial services are provided.</footer>
        </div>
      </main>

      {modal && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModal(false); }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="transfer-title"><button className="modal-close" onClick={() => setModal(false)} aria-label="Close">×</button><div className="modal-symbol">↗</div><h2 id="transfer-title">Make a transfer</h2><p>Move money between your demo accounts.</p><form onSubmit={submitTransfer}><label>From<select value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}>{accounts.map((a) => <option value={a.id} key={a.id}>{a.name} — {money(a.balance)}</option>)}</select></label><label>To<select value={form.to} onChange={(e) => setForm({ ...form, to: e.target.value })}>{accounts.map((a) => <option value={a.id} key={a.id}>{a.name}</option>)}</select></label><label>Amount<div className="amount-field"><span>$</span><input autoFocus type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required /></div></label><div className="modal-disclaimer">Demo only · No actual money will move.</div><button className="button button-primary full-button" type="submit">Confirm demo transfer</button></form></section></div>}
      {toast && <div className="toast" role="status">✓ &nbsp;{toast}</div>}
    </div>
  );
}

function TransactionList({ items }) {
  if (!items.length) return <div className="empty-state">No matching activity found.</div>;
  return <div className="transaction-list">{items.map((item) => <div className="transaction" key={item.id}><span className="transaction-icon">{item.icon}</span><span className="transaction-info"><b>{item.merchant}</b><small>{item.category} · {item.date}</small></span><span className="transaction-result"><b className={item.amount > 0 ? 'positive' : ''}>{item.amount > 0 ? '+' : '−'}{money(Math.abs(item.amount))}</b><small className={item.status === 'Pending' ? 'pending' : ''}>{item.status}</small></span></div>)}</div>;
}

export default App;
