import React, { useState, useRef, useEffect } from 'react';
import './chat.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function Message({ role, content }) {
  return (
    <div className={`message ${role}`}>
      <div className="role">{role}</div>
      <div className="content">{content}</div>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [githubMenuOpen, setGithubMenuOpen] = useState(false);
  const [repoDetailsDialogOpen, setRepoDetailsDialogOpen] = useState(false);
  const [reposList, setReposList] = useState([]);
  const [selectedRepoForDetails, setSelectedRepoForDetails] = useState('');
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [repoSelectOpen, setRepoSelectOpen] = useState(false);
  const [branchDetailsDialogOpen, setBranchDetailsDialogOpen] = useState(false);
  const [branchReposList, setBranchReposList] = useState([]);
  const [selectedBranchRepo, setSelectedBranchRepo] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  const [branchesList, setBranchesList] = useState([]);
  const [loadingBranchRepos, setLoadingBranchRepos] = useState(false);
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [branchRepoSelectOpen, setBranchRepoSelectOpen] = useState(false);
  const [branchNameSelectOpen, setBranchNameSelectOpen] = useState(false);
  const [editFilesDialogOpen, setEditFilesDialogOpen] = useState(false);
  const [editReposList, setEditReposList] = useState([]);
  const [selectedEditRepo, setSelectedEditRepo] = useState('');
  const [loadingEditRepos, setLoadingEditRepos] = useState(false);
  const [editRepoSelectOpen, setEditRepoSelectOpen] = useState(false);
  const [editMessage, setEditMessage] = useState('');
  const containerRef = useRef(null);
  const githubWrapperRef = useRef(null);
  const repoSelectRef = useRef(null);
  const branchRepoSelectRef = useRef(null);
  const branchNameSelectRef = useRef(null);
  const editRepoSelectRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [messages, loading]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (githubWrapperRef.current && !githubWrapperRef.current.contains(e.target)) {
        setGithubMenuOpen(false);
      }
      if (repoSelectOpen && repoSelectRef.current && !repoSelectRef.current.contains(e.target)) {
        setRepoSelectOpen(false);
      }
      if (branchRepoSelectOpen && branchRepoSelectRef.current && !branchRepoSelectRef.current.contains(e.target)) {
        setBranchRepoSelectOpen(false);
      }
      if (branchNameSelectOpen && branchNameSelectRef.current && !branchNameSelectRef.current.contains(e.target)) {
        setBranchNameSelectOpen(false);
      }
      if (editRepoSelectOpen && editRepoSelectRef.current && !editRepoSelectRef.current.contains(e.target)) {
        setEditRepoSelectOpen(false);
      }
    }
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [repoSelectOpen, branchRepoSelectOpen, branchNameSelectOpen, editRepoSelectOpen]);

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setInput('');
    setError(null);
    setLoading(true);

    const newMessages = [...messages, { role: 'user', content: trimmed }];
    setMessages(newMessages);

    try {
      const res = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          model: 'deepseek-r1:1.5b',
          history: newMessages.map(m => ({ role: m.role, content: m.content })),
          stream: false,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        const detail = data?.detail || 'Something went wrong';
        setError(detail);
        setMessages(msgs => [...msgs, { role: 'assistant', content: detail }]);
      } else {
        setMessages(msgs => [...msgs, { role: 'assistant', content: data.message }]);
      }
    } catch (err) {
      const msg =
        'Network error. Make sure FastAPI and Ollama are running.\nTry: uvicorn app:app --reload and ollama serve';
      setError(msg);
      setMessages(msgs => [...msgs, { role: 'assistant', content: msg }]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  async function openRepoDetailsDialog() {
    setGithubMenuOpen(false);
    setRepoDetailsDialogOpen(true);
    setSelectedRepoForDetails('');
    setRepoSelectOpen(false);
    setLoadingRepos(true);
    setReposList([]);
    try {
      const res = await fetch(`${API_BASE_URL}/github/repos?per_page=100`);
      const data = await res.json();
      if (res.ok && data.nodes && data.nodes.length) {
        setReposList(data.nodes);
        setSelectedRepoForDetails(data.nodes[0].name || '');
      } else {
        setReposList([]);
      }
    } catch (err) {
      setReposList([]);
    } finally {
      setLoadingRepos(false);
    }
  }

  function handleRepoDetailsOk() {
    if (!selectedRepoForDetails.trim()) return;
    send(`show details of repo ${selectedRepoForDetails}`);
    setRepoDetailsDialogOpen(false);
  }

  async function openBranchDetailsDialog() {
    setGithubMenuOpen(false);
    setBranchDetailsDialogOpen(true);
    setSelectedBranchRepo('');
    setSelectedBranch('');
    setBranchReposList([]);
    setBranchesList([]);
    setBranchRepoSelectOpen(false);
    setBranchNameSelectOpen(false);
    setLoadingBranchRepos(true);
    setLoadingBranches(false);
    try {
      const res = await fetch(`${API_BASE_URL}/github/repos?per_page=100`);
      const data = await res.json();
      if (res.ok && data.nodes && data.nodes.length) {
        setBranchReposList(data.nodes);
        setSelectedBranchRepo(data.nodes[0].name || '');
      } else {
        setBranchReposList([]);
      }
    } catch (err) {
      setBranchReposList([]);
    } finally {
      setLoadingBranchRepos(false);
    }
  }

  useEffect(() => {
    if (!branchDetailsDialogOpen || !selectedBranchRepo) return;
    const repo = branchReposList.find(r => r.name === selectedBranchRepo);
    if (!repo) {
      setBranchesList([]);
      setSelectedBranch('');
      return;
    }
    const owner = (repo.owner && repo.owner.login) || (repo.full_name && repo.full_name.split('/')[0]) || '';
    if (!owner) {
      setBranchesList([]);
      setSelectedBranch('');
      return;
    }
    setLoadingBranches(true);
    setSelectedBranch('');
    fetch(`${API_BASE_URL}/github/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo.name)}/branches`)
      .then(r => r.json())
      .then(data => {
        const branches = (data && data.branches) || [];
        setBranchesList(branches);
        if (branches.length) setSelectedBranch(branches[0].name || '');
      })
      .catch(() => setBranchesList([]))
      .finally(() => setLoadingBranches(false));
  }, [branchDetailsDialogOpen, selectedBranchRepo, branchReposList]);

  function handleBranchDetailsOk() {
    if (!selectedBranchRepo.trim() || !selectedBranch.trim()) return;
    send(`show the ${selectedBranch} branch of ${selectedBranchRepo} repo`);
    setBranchDetailsDialogOpen(false);
  }

  async function openEditFilesDialog() {
    setGithubMenuOpen(false);
    setEditFilesDialogOpen(true);
    setSelectedEditRepo('');
    setEditMessage('');
    setEditReposList([]);
    setEditRepoSelectOpen(false);
    setLoadingEditRepos(true);
    try {
      const res = await fetch(`${API_BASE_URL}/github/repos?per_page=100`);
      const data = await res.json();
      if (res.ok && data.nodes && data.nodes.length) {
        setEditReposList(data.nodes);
        setSelectedEditRepo(data.nodes[0].name || '');
      } else {
        setEditReposList([]);
      }
    } catch (err) {
      setEditReposList([]);
    } finally {
      setLoadingEditRepos(false);
    }
  }

  function handleGithubAction(action) {
    setGithubMenuOpen(false);
    if (action === 'show-all-repos') {
      send('show me all my github repos');
    } else if (action === 'show-repo-details') {
      openRepoDetailsDialog();
    } else if (action === 'show-branch-details') {
      openBranchDetailsDialog();
    } else if (action === 'create-pr') {
      openEditFilesDialog();
    }
  }

  return (
    <div className="chat-root">
      <div className="chat-container" ref={containerRef}>
        {messages.map((m, idx) => (
          <Message key={idx} role={m.role} content={m.content} />
        ))}
        {loading && <Message role="assistant" content="…" />}
      </div>

      <div className="input-area">
        <form className="input-form" onSubmit={handleSubmit}>
          <div className="input-row">
            <div className="github-feature-wrapper" ref={githubWrapperRef}>
              <button
                type="button"
                className="github-feature-btn"
                onClick={() => setGithubMenuOpen(open => !open)}
              >
                GitHub Feature
              </button>
              {githubMenuOpen && (
                <div className="github-dropdown">
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('show-all-repos')}
                  >
                    Show all github repos
                  </button>
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('show-repo-details')}
                  >
                    Show repo details
                  </button>
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('show-branch-details')}
                  >
                    Show branch details
                  </button>
                  <button
                    type="button"
                    className="github-dropdown-item"
                    onClick={() => handleGithubAction('create-pr')}
                  >
                    Edit Files
                  </button>
                </div>
              )}
            </div>

            <textarea
              className="message-input"
              placeholder="Type your message..."
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
            />
            <button type="submit" className="send-btn" disabled={loading}>
              Send
            </button>
          </div>
        </form>
        {error && <div className="error-banner">{error}</div>}
      </div>

      {editFilesDialogOpen && (
        <div className="dialog-backdrop" onClick={() => setEditFilesDialogOpen(false)}>
          <div className="dialog-box" onClick={e => e.stopPropagation()}>
            <h3 className="dialog-title">Edit files</h3>
            <p className="dialog-label">Select repository</p>
            {loadingEditRepos ? (
              <p className="dialog-loading">Loading repositories…</p>
            ) : (
              <div className="dialog-select-wrapper" ref={editRepoSelectRef}>
                <button
                  type="button"
                  className="dialog-select-trigger"
                  onClick={() => setEditRepoSelectOpen(o => !o)}
                  aria-expanded={editRepoSelectOpen}
                >
                  {selectedEditRepo
                    ? editReposList.find(r => r.name === selectedEditRepo)?.full_name || selectedEditRepo
                    : '-- Select repo --'}
                </button>
                {editRepoSelectOpen && (
                  <ul className="dialog-select-list" role="listbox">
                    {editReposList.map(repo => (
                      <li
                        key={repo.id}
                        role="option"
                        aria-selected={selectedEditRepo === repo.name}
                        className={`dialog-select-option ${selectedEditRepo === repo.name ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedEditRepo(repo.name);
                          setEditRepoSelectOpen(false);
                        }}
                      >
                        {repo.full_name || repo.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <p className="dialog-label">Describe the changes you want</p>
            <textarea
              className="dialog-textarea"
              rows={5}
              value={editMessage}
              onChange={e => setEditMessage(e.target.value)}
              placeholder="Describe what changes you want in this repository..."
            />
            <div className="dialog-actions">
              <button
                type="button"
                className="dialog-btn dialog-cancel"
                onClick={() => setEditFilesDialogOpen(false)}
              >
                Cancel
              </button>
              <button type="button" className="dialog-btn dialog-ok">
                Commit changes and create PR
              </button>
            </div>
          </div>
        </div>
      )}

      {branchDetailsDialogOpen && (
        <div className="dialog-backdrop" onClick={() => setBranchDetailsDialogOpen(false)}>
          <div className="dialog-box" onClick={e => e.stopPropagation()}>
            <h3 className="dialog-title">Show branch details</h3>
            <p className="dialog-label">Select repository</p>
            {loadingBranchRepos ? (
              <p className="dialog-loading">Loading repositories…</p>
            ) : (
              <div className="dialog-select-wrapper" ref={branchRepoSelectRef}>
                <button
                  type="button"
                  className="dialog-select-trigger"
                  onClick={() => setBranchRepoSelectOpen(o => !o)}
                  aria-expanded={branchRepoSelectOpen}
                >
                  {selectedBranchRepo
                    ? branchReposList.find(r => r.name === selectedBranchRepo)?.full_name || selectedBranchRepo
                    : '-- Select repo --'}
                </button>
                {branchRepoSelectOpen && (
                  <ul className="dialog-select-list" role="listbox">
                    {branchReposList.map(repo => (
                      <li
                        key={repo.id}
                        role="option"
                        aria-selected={selectedBranchRepo === repo.name}
                        className={`dialog-select-option ${selectedBranchRepo === repo.name ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedBranchRepo(repo.name);
                          setBranchRepoSelectOpen(false);
                        }}
                      >
                        {repo.full_name || repo.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <p className="dialog-label">Select branch</p>
            {loadingBranches ? (
              <p className="dialog-loading">Loading branches…</p>
            ) : (
              <div className="dialog-select-wrapper" ref={branchNameSelectRef}>
                <button
                  type="button"
                  className="dialog-select-trigger"
                  onClick={() => setBranchNameSelectOpen(o => !o)}
                  aria-expanded={branchNameSelectOpen}
                >
                  {selectedBranch || '-- Select branch --'}
                </button>
                {branchNameSelectOpen && (
                  <ul className="dialog-select-list" role="listbox">
                    {branchesList.map(b => (
                      <li
                        key={b.name}
                        role="option"
                        aria-selected={selectedBranch === b.name}
                        className={`dialog-select-option ${selectedBranch === b.name ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedBranch(b.name);
                          setBranchNameSelectOpen(false);
                        }}
                      >
                        {b.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <div className="dialog-actions">
              <button type="button" className="dialog-btn dialog-cancel" onClick={() => setBranchDetailsDialogOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="dialog-btn dialog-ok"
                onClick={handleBranchDetailsOk}
                disabled={loadingBranchRepos || loadingBranches || !selectedBranchRepo || !selectedBranch}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}

      {repoDetailsDialogOpen && (
        <div className="dialog-backdrop" onClick={() => setRepoDetailsDialogOpen(false)}>
          <div className="dialog-box" onClick={e => e.stopPropagation()}>
            <h3 className="dialog-title">Show repository details</h3>
            <p className="dialog-label">Select repository</p>
            {loadingRepos ? (
              <p className="dialog-loading">Loading repositories…</p>
            ) : (
              <div className="dialog-select-wrapper" ref={repoSelectRef}>
                <button
                  type="button"
                  className="dialog-select-trigger"
                  onClick={() => setRepoSelectOpen(o => !o)}
                  aria-expanded={repoSelectOpen}
                  aria-haspopup="listbox"
                >
                  {selectedRepoForDetails
                    ? reposList.find(r => r.name === selectedRepoForDetails)?.full_name || selectedRepoForDetails
                    : '-- Select repo --'}
                </button>
                {repoSelectOpen && (
                  <ul className="dialog-select-list" role="listbox">
                    {reposList.map(repo => (
                      <li
                        key={repo.id}
                        role="option"
                        aria-selected={selectedRepoForDetails === repo.name}
                        className={`dialog-select-option ${selectedRepoForDetails === repo.name ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedRepoForDetails(repo.name);
                          setRepoSelectOpen(false);
                        }}
                      >
                        {repo.full_name || repo.name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            <div className="dialog-actions">
              <button type="button" className="dialog-btn dialog-cancel" onClick={() => setRepoDetailsDialogOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="dialog-btn dialog-ok"
                onClick={handleRepoDetailsOk}
                disabled={loadingRepos || !selectedRepoForDetails}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

