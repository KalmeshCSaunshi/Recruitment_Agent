document.addEventListener('DOMContentLoaded', () => {
    const jdInput = document.getElementById('jd-input');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const analyzeBtn = document.getElementById('analyze-btn');
    const sourceBtn = document.getElementById('source-btn');
    const marketBtn = document.getElementById('market-btn');
    const resultsSection = document.getElementById('results-section');
    const loader = document.getElementById('loader');
    const resultsGrid = document.getElementById('results-grid');
    const fileListContainer = document.getElementById('file-list');
    const progressBar = document.getElementById('progress-bar');
    const loadingText = document.getElementById('loading-text');
    let currentPage = 1;
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    let selectedFiles = [];

    // Tab Switching Logic
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content views
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${targetTab}-view`) {
                    content.classList.add('active');
                }
            });

            // Clear results when switching modes
            resultsSection.classList.add('hidden');
            resultsGrid.innerHTML = '';
            validateForm();
        });
    });

    // Handle Drag and Drop
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleFiles(Array.from(e.dataTransfer.files));
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFiles(Array.from(e.target.files));
        }
    });

    // function handleFiles(files) {
    //     const validFiles = files.filter(f => f.type === 'application/pdf');

    //     if (validFiles.length < files.length) {
    //         alert('Some files were skipped. Only PDF files are supported.');
    //     }
    // HANDELS BOTH PDF AND DOCX FILES 
    function handleFiles(files) {
        const validFiles = files.filter(f =>
            f.type === 'application/pdf' ||
            f.name.toLowerCase().endsWith('.docx') ||
            f.name.toLowerCase().endsWith('.doc')
        );

        if (validFiles.length < files.length) {
            alert('Some files were skipped. Only PDF and Word files are supported.');
        }


        const remainingSlots = 10 - selectedFiles.length;
        const filesToAdd = validFiles.slice(0, remainingSlots);

        selectedFiles = [...selectedFiles, ...filesToAdd];
        renderFileList();
        validateForm();
    }

    function renderFileList() {
        if (selectedFiles.length === 0) {
            fileListContainer.classList.add('hidden');
            dropZone.querySelector('p').classList.remove('hidden');
            dropZone.querySelector('.drop-icon').classList.remove('hidden');
            return;
        }

        fileListContainer.classList.remove('hidden');
        dropZone.querySelector('p').classList.add('hidden');
        dropZone.querySelector('.drop-icon').classList.add('hidden');

        fileListContainer.innerHTML = '';
        selectedFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.innerHTML = `
                <span>${file.name}</span>
                <button class="remove-file" data-index="${index}">✕</button>
            `;
            fileListContainer.appendChild(item);
        });

        document.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.getAttribute('data-index'));
                selectedFiles.splice(index, 1);
                renderFileList();
                validateForm();
            });
        });
    }

    jdInput.addEventListener('input', validateForm);

    function validateForm() {
        const jdFilled = jdInput.value.trim().length > 0;

        analyzeBtn.disabled = !(jdFilled && selectedFiles.length > 0);
        sourceBtn.disabled = !jdFilled;
        if (marketBtn) marketBtn.disabled = !jdFilled;
    }

    analyzeBtn.addEventListener('click', async () => {
        if (!jdInput.value || selectedFiles.length === 0) return;

        resultsSection.classList.remove('hidden');
        resultsGrid.innerHTML = '';
        loader.classList.remove('hidden');
        analyzeBtn.disabled = true;

        const total = selectedFiles.length;
        let completed = 0;

        // BATCH PROCESSING: Send all resumes in one single request
        loadingText.textContent = `Analyzing ${total} resumes in parallel...`;

        const formData = new FormData();
        formData.append('jd', jdInput.value);
        for (let i = 0; i < total; i++) {
            formData.append('resumes', selectedFiles[i]);
        }

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Server error');

            // STREAMING READER
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // Process all complete lines
                for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;

                    try {
                        const data = JSON.parse(line);
                        completed++;
                        const progress = (completed / total) * 100;
                        progressBar.style.width = `${progress}%`;
                        loadingText.textContent = `Processing (${completed}/${total})...`;

                        if (data.error) {
                            addErrorCard(data.error, data.filename);
                        } else {
                            addResultCard(data, data.filename);
                        }
                    } catch (e) {
                        console.error('Parse error on line:', line, e);
                    }
                }
                // Keep the partial line in the buffer
                buffer = lines[lines.length - 1];
            }

        } catch (error) {
            console.error('Streaming Error:', error);
            addErrorCard(error.message, "Batch Stream");
        } finally {
            analyzeBtn.disabled = false;
            loader.classList.add('hidden');

            // Clear files for next batch
            selectedFiles = [];
            renderFileList();
            validateForm();
        }
    });

    // Sourcing Action
    sourceBtn.addEventListener('click', async () => {
        console.log("Sourcing button clicked!");
        resultsSection.classList.remove('hidden');
        resultsGrid.innerHTML = '';
        loader.classList.remove('hidden');
        loadingText.textContent = 'Extracting keywords and searching Naukri...';
        sourceBtn.disabled = true;

        const formData = new FormData();
        formData.append('jd', jdInput.value);
        formData.append('page', currentPage);

        console.log("Sending request to /api/source...");
        try {
            const response = await fetch('/api/source', {
                method: 'POST',
                body: formData
            });

            const data = await response.json() || {};

            if (response.ok) {
                // Display search info
                const infoCard = document.createElement('div');
                infoCard.className = 'candidate-card glass';
                infoCard.style.borderStyle = 'dashed';

                const keywords = data.keywords_used || [];
                const boolean = data.boolean_query || 'No query generated';
                const searchUrl = data.search_url || 'https://resdex.naukri.com/v3';

                infoCard.innerHTML = `
                    <div class="candidate-header">
                        <div class="candidate-info">
                            <h2>Sourcing Leads via Naukri</h2>
                            <p><strong>Primary Keywords:</strong> ${keywords.length > 0 ? keywords.map(k => `<span class="model-tag">${k}</span>`).join(' ') : 'None'}</p>
                            <div class="scoring-logic" style="margin-top: 1rem;">
                                <strong>Generated Boolean Search:</strong>
                                <p style="font-family: monospace; font-size: 0.8rem; margin-top: 0.5rem; color: var(--accent);">${boolean}</p>
                            </div>
                        </div>
                    </div>
                    <div class="candidate-body">
                        <p>I have generated a targeted search for you. You can also view the full results here: 
                           <a href="${searchUrl}" target="_blank" style="color: var(--accent)">Open Resdex Search</a>
                        </p>
                    </div>
                `;
                resultsGrid.appendChild(infoCard);

                // Display individual leads
                const leads = data.simulated_leads || [];
                leads.forEach(lead => {
                    if (lead) addLeadCard(lead);
                });

                // Add Next Page Button
                if (data.simulated_leads.length > 0) {
                    const nextBtn = document.createElement('button');
                    nextBtn.className = 'secondary-btn';
                    nextBtn.style.marginTop = '2rem';
                    nextBtn.style.width = '100%';
                    nextBtn.innerHTML = '➡️ Load Next Page from Naukri';
                    nextBtn.onclick = () => {
                        currentPage++;
                        sourceBtn.click();
                    };
                    resultsGrid.appendChild(nextBtn);
                }

                // Display "Other Candidates" pool table
                const otherCandidates = data.other_candidates || [];
                if (otherCandidates.length > 0) {
                    const poolCard = document.createElement('div');
                    poolCard.className = 'candidate-card glass';
                    poolCard.style.marginTop = '2rem';
                    const rows = otherCandidates.map((c, i) => `
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.07);">
                            <td style="padding: 8px 4px; color: var(--text-secondary);">${i + 11}</td>
                            <td style="padding: 8px 4px; font-weight: 600;">${c.name}</td>
                            <td style="padding: 8px 4px; color: var(--text-secondary);">${c.exp}</td>
                            <td style="padding: 8px 4px; color: var(--text-secondary);">NP: ${c.notice_period}</td>
                            <td style="padding: 8px 4px; text-align: right;">
                                <a href="${c.link}" target="_blank" style="color: var(--accent); font-size: 0.85rem; font-weight: 600; text-decoration: none; padding: 4px 10px; border: 1px solid var(--accent); border-radius: 4px;">Open Profile ↗</a>
                            </td>
                        </tr>
                    `).join('');
                    poolCard.innerHTML = `
                        <div class="candidate-header">
                            <div class="candidate-info">
                                <h2>👥 Other Candidates in Pool</h2>
                                <span class="filename">${otherCandidates.length} more candidates found on this page — click to open their Resdex profile</span>
                            </div>
                        </div>
                        <div class="candidate-body">
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                                <thead>
                                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.15);">
                                        <th style="padding: 6px 4px; text-align: left; color: var(--text-secondary); font-weight: 500;">#</th>
                                        <th style="padding: 6px 4px; text-align: left; color: var(--text-secondary); font-weight: 500;">Name</th>
                                        <th style="padding: 6px 4px; text-align: left; color: var(--text-secondary); font-weight: 500;">Experience</th>
                                        <th style="padding: 6px 4px; text-align: left; color: var(--text-secondary); font-weight: 500;">Notice Period</th>
                                        <th style="padding: 6px 4px; text-align: right; color: var(--text-secondary); font-weight: 500;">Profile</th>
                                    </tr>
                                </thead>
                                <tbody>${rows}</tbody>
                            </table>
                        </div>
                    `;
                    resultsGrid.appendChild(poolCard);
                }
            } else {
                addErrorCard(data.error || 'Sourcing failed', 'Naukri Sourcing');
            }
        } catch (error) {
            console.error('Sourcing Error:', error);
            addErrorCard(error.message, "Naukri Sourcing");
        } finally {
            sourceBtn.disabled = false;
            loader.classList.add('hidden');
        }
    });

    // Market Analysis → Show in UI, then allow Download
    let marketData = null; // store latest scan results

    if (marketBtn) {
        marketBtn.addEventListener('click', async () => {
            const jd = jdInput.value.trim();
            if (!jd) return;

            marketBtn.disabled = true;
            marketBtn.textContent = '⏳ Scanning Naukri... (2-3 min)';

            // Clear any previous market results
            const oldMarket = document.getElementById('market-results-section');
            if (oldMarket) oldMarket.remove();

            try {
                const response = await fetch('/api/market-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jd })
                });

                if (response.ok) {
                    const data = await response.json();
                    marketData = data;
                    renderMarketResults(data, jd);
                    marketBtn.textContent = '🔄 Re-scan Market';
                } else if (response.status === 429) {
                    const err = await response.json();
                    alert('⚠️ ' + (err.error || 'Naukri browser is busy. Wait and try again.'));
                    marketBtn.textContent = '📊 Market Analysis';
                } else {
                    const err = await response.json();
                    alert('Market Analysis failed: ' + (err.error || 'Unknown error'));
                    marketBtn.textContent = '📊 Market Analysis';
                }
            } catch (error) {
                console.error('Market Analysis Error:', error);
                alert('Error: ' + error.message);
                marketBtn.textContent = '📊 Market Analysis';
            } finally {
                marketBtn.disabled = false;
            }
        });
    }

    function renderMarketResults(data, jd) {
        const candidates = data.top_candidates || data.candidates || [];
        const s = data.summary || {};
        const dist = s.exp_distribution || {};
        const matchDist = s.match_distribution || {};
        const targetRange = s.jd_target_range || '';
        const inTarget = s.in_target_range || 0;
        const score = s.availability_score || 0;
        const tightness = s.tightness || 'Unknown';
        const companies = s.top_companies || [];
        const cities = s.top_cities || [];
        const topSkills = s.top_skills || [];
        const narrative = s.narrative || '';
        const total = s.total || 0;
        const avgMatch = s.avg_match_score || 0;
        const highQuality = s.high_quality_pool || 0;
        const marketHealth = s.market_health || '';
        const hiringDiff = s.hiring_difficulty || '';
        const activeHQ = s.active_high_quality_pool || 0;
        const immediatePool = s.immediate_joiner_pool || 0;

        const tightnessColor = {
            'High Supply': '#10b981', 'Moderate Supply': '#f59e0b',
            'Low Supply': '#f97316', 'Scarce': '#ef4444'
        }[tightness] || '#8b5cf6';

        const healthColor = { 'Strong': '#10b981', 'Moderate': '#f59e0b', 'Tight': '#f97316', 'Scarce': '#ef4444' }[marketHealth] || '#8b5cf6';
        const diffColor  = { 'Low': '#10b981', 'Medium': '#f59e0b', 'High': '#f97316', 'Very High': '#ef4444' }[hiringDiff] || '#8b5cf6';
        const scoreColor = score >= 60 ? '#10b981' : score >= 35 ? '#f59e0b' : '#ef4444';
        const avgColor   = avgMatch >= 70 ? '#10b981' : avgMatch >= 50 ? '#f59e0b' : '#ef4444';

        // Target buckets detection
        const [jlo, jhi] = targetRange.replace(' years','').split('-').map(Number);
        const maxBucketVal = Math.max(...Object.values(dist), 1);
        const maxMatchVal  = Math.max(...Object.values(matchDist), 1);

        const section = document.createElement('div');
        section.id = 'market-results-section';
        section.className = 'market-report-section';

        section.innerHTML = `
        <div class="mr-header">
            <div class="mr-title-block">
                <div class="mr-label">TALENT MARKET INTELLIGENCE REPORT</div>
                <h2 class="mr-title">Market Analysis</h2>
                <div class="mr-meta">Search: <code>${s.query || ''}</code> &nbsp;|&nbsp; Generated: ${s.generated || ''}</div>
            </div>
            <button id="download-market-xl" class="download-xl-btn">⬇️ Export Excel</button>
        </div>

        <!-- KPI Cards Row 1 — Pool & Availability -->
        <div class="mr-cards">
            <div class="mr-card">
                <div class="mr-card-value" style="color:${scoreColor}">${score}<span class="mr-card-unit">/100</span></div>
                <div class="mr-card-label">Availability Score</div>
                <div class="mr-progress-track"><div class="mr-progress-fill" style="width:${score}%;background:${scoreColor}"></div></div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:${avgColor}">${avgMatch}<span class="mr-card-unit">%</span></div>
                <div class="mr-card-label">Avg Match Score</div>
                <div class="mr-card-sub">${highQuality} candidates @ 80%+</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:#8b5cf6">${total}</div>
                <div class="mr-card-label">Total Talent Pool</div>
                <div class="mr-tightness-badge" style="background:${tightnessColor}22;border-color:${tightnessColor};color:${tightnessColor}">${tightness}</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:#10b981">${s.active_30d || 0}</div>
                <div class="mr-card-label">Active Last 30 Days</div>
                <div class="mr-card-sub">${total ? Math.round((s.active_30d||0)/total*100) : 0}% of pool</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:#f59e0b">${s.notice_30d || 0}</div>
                <div class="mr-card-label">Short Notice (≤30d)</div>
                <div class="mr-card-sub">${immediatePool} high-match immediate</div>
            </div>
        </div>

        <!-- KPI Cards Row 2 — Intelligence Metrics -->
        <div class="mr-cards" style="margin-top:0.75rem">
            <div class="mr-card">
                <div class="mr-card-value" style="color:${healthColor}">${marketHealth || '—'}</div>
                <div class="mr-card-label">Market Health</div>
                <div class="mr-card-sub">${inTarget} in target exp range</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:${diffColor}">${hiringDiff || '—'}</div>
                <div class="mr-card-label">Hiring Difficulty</div>
                <div class="mr-card-sub">Based on quality + activity</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:#6366f1">${highQuality}</div>
                <div class="mr-card-label">High Quality Pool</div>
                <div class="mr-card-sub">${activeHQ} active &amp; high-match</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:#06b6d4">${inTarget}</div>
                <div class="mr-card-label">Target Range Match</div>
                <div class="mr-card-sub">${targetRange}</div>
            </div>
            <div class="mr-card">
                <div class="mr-card-value" style="color:#10b981">${immediatePool}</div>
                <div class="mr-card-label">Immediate Joiners</div>
                <div class="mr-card-sub">60%+ match + short notice</div>
            </div>
        </div>

        <!-- AI Narrative -->
        ${narrative ? `<div class="mr-narrative">
            <div class="mr-section-label">📝 ANALYST BRIEF</div>
            <p class="mr-narrative-text">${narrative}</p>
        </div>` : ''}

        <!-- Charts Row 1: Match Distribution + Experience Distribution -->
        <div class="mr-charts-row">
            <!-- Match Score Distribution -->
            ${Object.keys(matchDist).length ? `<div class="mr-chart-panel">
                <div class="mr-section-label">🎯 MATCH SCORE DISTRIBUTION</div>
                <div class="mr-bar-chart">
                    ${Object.entries(matchDist).map(([k, v]) => {
                        const pct = Math.round(v / maxMatchVal * 100);
                        const col = k === '90-100' ? '#10b981' : k === '80-89' ? '#6366f1' : k === '70-79' ? '#f59e0b' : k === '60-69' ? '#f97316' : '#ef4444';
                        return `<div class="mr-bar-row">
                            <div class="mr-bar-label">${k}%</div>
                            <div class="mr-bar-track">
                                <div class="mr-bar-fill" style="width:${pct}%;background:${col}"></div>
                            </div>
                            <div class="mr-bar-count">${v}</div>
                        </div>`;
                    }).join('')}
                </div>
            </div>` : ''}

            <!-- Experience Distribution -->
            <div class="mr-chart-panel">
                <div class="mr-section-label">📊 EXPERIENCE DISTRIBUTION</div>
                <div class="mr-bar-chart">
                    ${Object.entries(dist).map(([k, v]) => {
                        const pct = Math.round(v / maxBucketVal * 100);
                        const lo = parseInt(k);
                        const isTarget = lo >= jlo && lo < jhi + 2;
                        return `<div class="mr-bar-row">
                            <div class="mr-bar-label ${isTarget ? 'mr-bar-label-target' : ''}">${k} ${isTarget ? '🎯' : ''}</div>
                            <div class="mr-bar-track">
                                <div class="mr-bar-fill ${isTarget ? 'mr-bar-fill-target' : ''}" style="width:${pct}%"></div>
                            </div>
                            <div class="mr-bar-count">${v}</div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
        </div>

        <!-- Charts Row 2: Top Skills + Companies + Cities -->
        <div class="mr-charts-row">
            <!-- Top Skills -->
            ${topSkills.length ? `<div class="mr-chart-panel">
                <div class="mr-section-label">💡 TOP SKILLS IN MARKET</div>
                <div class="mr-bar-chart">
                    ${topSkills.map(sk => {
                        const pct = Math.round(sk.count / (topSkills[0]?.count || 1) * 100);
                        return `<div class="mr-bar-row">
                            <div class="mr-bar-label">${sk.name}</div>
                            <div class="mr-bar-track">
                                <div class="mr-bar-fill" style="width:${pct}%;background:#a78bfa"></div>
                            </div>
                            <div class="mr-bar-count">${sk.count}</div>
                        </div>`;
                    }).join('')}
                </div>
            </div>` : ''}

            <!-- Top Companies -->
            ${companies.length ? `<div class="mr-chart-panel">
                <div class="mr-section-label">🏢 TOP TALENT SOURCES</div>
                <div class="mr-bar-chart">
                    ${companies.map(c => {
                        const pct = Math.round(c.count / (companies[0]?.count || 1) * 100);
                        return `<div class="mr-bar-row">
                            <div class="mr-bar-label">${c.name}</div>
                            <div class="mr-bar-track">
                                <div class="mr-bar-fill" style="width:${pct}%;background:#6366f1"></div>
                            </div>
                            <div class="mr-bar-count">${c.count}</div>
                        </div>`;
                    }).join('')}
                </div>
            </div>` : ''}

            <!-- Top Cities -->
            ${cities.length ? `<div class="mr-chart-panel">
                <div class="mr-section-label">📍 GEOGRAPHIC DISTRIBUTION</div>
                <div class="mr-bar-chart">
                    ${cities.map(c => {
                        const pct = Math.round(c.count / (cities[0]?.count || 1) * 100);
                        return `<div class="mr-bar-row">
                            <div class="mr-bar-label">${c.name}</div>
                            <div class="mr-bar-track">
                                <div class="mr-bar-fill" style="width:${pct}%;background:#06b6d4"></div>
                            </div>
                            <div class="mr-bar-count">${c.count}</div>
                        </div>`;
                    }).join('')}
                </div>
            </div>` : ''}
        </div>

        <!-- Top 20 Candidates Table -->
        <div class="mr-section-label" style="margin-top:1.5rem">👥 TOP ${candidates.length} MATCHED CANDIDATES (of ${total} scanned)</div>
        <div class="market-table-wrap">
            <table class="market-table">
                <thead>
                    <tr>
                        <th>#</th><th>Name</th><th>Match %</th><th>Exp</th>
                        <th>Active Status</th><th>Notice</th><th>Company / Role</th>
                        <th>Location</th><th>Matched Skills</th><th>Profile</th>
                    </tr>
                </thead>
                <tbody>
                    ${candidates.map((c, i) => {
                        const mp = c.match_percentage || 0;
                        const mpClass = mp >= 80 ? 'match-high' : mp >= 60 ? 'match-medium' : 'match-low';
                        let rowClass = c.in_target_range
                            ? (c.is_active_30d === true ? 'row-active' : 'row-target')
                            : (mp < 40 ? 'row-other-exp' : '');
                        const badge = c.in_target_range ? '<span class="target-badge">🎯</span>' : '';
                        const skillsDisplay = (c.matched_skills || []).length
                            ? c.matched_skills.slice(0,4).join(', ') + (c.matched_skills.length > 4 ? ` +${c.matched_skills.length-4}` : '')
                            : (c.skills || 'N/A');
                        const link = c.profile_link
                            ? `<a href="${c.profile_link}" target="_blank" class="profile-link-btn">Open ↗</a>`
                            : '—';
                        return `<tr class="${rowClass}">
                            <td>${i+1}</td>
                            <td><strong>${c.name}</strong>${badge}</td>
                            <td><span class="match-pill ${mpClass}">${mp}%</span></td>
                            <td>${c.experience||'N/A'}</td>
                            <td>${c.active_status||'Unknown'}</td>
                            <td>${c.notice_period||'N/A'}</td>
                            <td>${c.current||'N/A'}</td>
                            <td>${c.location||'N/A'}</td>
                            <td class="skills-cell">${skillsDisplay}</td>
                            <td>${link}</td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
        </div>`;

        const container = document.querySelector('.container');
        const old = document.getElementById('market-results-section');
        if (old) old.remove();
        container.appendChild(section);
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Download handler
        document.getElementById('download-market-xl').addEventListener('click', async () => {
            const btn = document.getElementById('download-market-xl');
            btn.disabled = true;
            btn.textContent = '⏳ Generating...';
            try {
                const exportData = {
                    candidates: data.top_candidates || data.candidates || [],
                    summary: data.summary,
                    jd_snippet: jd.substring(0, 60)
                };
                const res = await fetch('/api/export-market-excel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(exportData)
                });
                if (res.ok) {
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    const nm = (res.headers.get('Content-Disposition') || '').match(/filename="?([^"]+)"?/);
                    a.download = nm ? nm[1] : 'Market_Analysis.xlsx';
                    document.body.appendChild(a); a.click(); a.remove();
                    window.URL.revokeObjectURL(url);
                    btn.textContent = '✅ Downloaded!';
                } else { btn.textContent = '⬇️ Export Excel'; alert('Export failed'); }
            } catch (e) { btn.textContent = '⬇️ Export Excel'; alert('Export error: ' + e.message); }
            finally { btn.disabled = false; }
        });
    }



    function addLeadCard(lead) {

        if (!lead) return;
        const card = document.createElement('div');
        card.className = 'candidate-card glass';

        const name = lead.name || 'Unknown Candidate';
        const exp = lead.exp || 'N/A Exp';
        const np = lead.notice_period || 'N/A';
        const score = lead.match_percentage || 0;
        const evidence = lead.context_evidence || 'No evidence extracted.';
        const phone = lead.phone || 'N/A';
        const email = lead.email || 'N/A';
        const skills = lead.matched_skills || [];
        const link = lead.link || '#';
        const requirementsAnalysis = lead.requirements_analysis || [];
        const projectInsights = lead.project_insights || [];

        const candidateId = encodeURIComponent(name.replace(/\s+/g, '_').toLowerCase());
        card.setAttribute('data-candidate-id', candidateId);

        const scoreClass = score >= 75 ? 'excellent' : (score >= 50 ? 'average' : 'poor');

        const reqRows = requirementsAnalysis.map(req => {
            const yrs = req.years_of_experience;
            const yrsDisplay = (yrs === null || yrs === undefined || yrs === 'N/A') ? 'N/A' : (yrs === 0 ? '< 1y' : `${yrs}y`);
            return `
            <li>
                <strong>${req.requirement || 'Unknown requirement'}</strong>
                ${req.is_mandatory ? '<span class="mandatory-tag">MANDATORY</span>' : ''}
                <br>
                Status: <span class="status-${(req.status || 'unknown').toLowerCase()}">${req.status || 'unknown'}</span>
                • <strong>Exp: ${yrsDisplay}</strong>
                ${req.evidence ? `<span class="evidence">"${req.evidence}"</span>` : ''}
            </li>
        `}).join('');

        const projectRows = projectInsights.map(p => `
            <li>
                <strong>${p.name || 'Project'}</strong>
                <br>
                <p>${p.description || ''}</p>
            </li>
        `).join('');

        const b = {
            mandatory_score: `${score}%`,
            projects_score: `${projectInsights.length} Projects`,
            depth_score: `N/A`,
            logic_explanation: lead.scoring_logic || 'Deterministic keyword match on Resdex profile.'
        };

        const key = `candidate_feedback_${candidateId}`;
        const savedData = JSON.parse(localStorage.getItem(key) || '{}');
        const savedNotes = savedData.notes || '';

        const feed = lead.feedback || {};
        const bullets = feed.evaluation_bullets || [];
        let bulletsHtml = '';
        if (bullets.length > 0) {
            bulletsHtml = bullets.map(b => `
                <li style="margin-bottom: 8px; line-height: 1.45; color: var(--text-primary); font-size: 0.9rem; text-align: justify;">
                    ${b}
                </li>
            `).join('');
        } else {
            bulletsHtml = `<li style="color: var(--text-secondary); font-size: 0.85rem; font-style: italic;">No evaluation feedback generated.</li>`;
        }

        const feedbackBoxHtml = `
        <div class="agent-feedback-block" style="background: rgba(255, 255, 255, 0.02); border-left: 4px solid var(--accent); padding: 16px 20px; border-radius: 8px; margin-top: 1.2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h4 style="margin: 0 0 12px 0; color: var(--accent); display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 6px;">
                🤖 AI Agent Evaluation
            </h4>
            <ul style="margin: 0; padding-left: 1.1rem; list-style-type: square;">
                ${bulletsHtml}
            </ul>
        </div>`;

        card.innerHTML = `
            <div class="candidate-header">
                <div class="candidate-info">
                    <h2>${name}</h2>
                    <span class="filename">${exp} • NP: ${np} • 🕒 Active: ${lead.active_status || 'N/A'}</span>
                </div>
                <div class="candidate-score ${scoreClass}">
                    <span class="val">${score}</span><span class="total">%</span>
                </div>
            </div>
            <div class="candidate-body">
                <div class="candidate-summary">
                    <h4>Executive Summary</h4>
                    <p>${lead.context_evidence || 'Sourced from Naukri Resdex.'}</p>
                    <div class="scoring-logic">
                        <strong>Scoring Breakdown:</strong>
                        <div class="breakdown-pills">
                            <span class="pill">Score: ${b.mandatory_score}</span>
                            <span class="pill">Projects: ${b.projects_score}</span>
                            <span class="pill">Depth: ${b.depth_score}</span>
                        </div>
                        <p>${b.logic_explanation}</p>
                    </div>
                    
                    ${feedbackBoxHtml}
                </div>
                <div class="candidate-details">
                    <h4>📋 Requirements Check</h4>
                    <ul>${reqRows || '<li>No requirement analysis available.</li>'}</ul>
                </div>
                <div class="candidate-details">
                    <h4>🚀 Relevant Projects</h4>
                    <ul>${projectRows || '<li>No explicit project details found for the mandatory skills.</li>'}</ul>
                </div>

                <div class="candidate-details" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.15);">
                    <a href="${link}" target="_blank" class="primary-btn" style="text-decoration: none; text-align: center; display: block; background: var(--accent);">
                        🚀 View Full Resdex Profile
                    </a>
                </div>
            </div>
        `;
        resultsGrid.appendChild(card);
    }

    function addResultCard(data, filename) {
        const card = document.createElement('div');
        card.className = 'candidate-card glass';

        // 1. Requirements (Mapping Agentic fields to your layout)
        const reqRows = (data.requirements_analysis || []).map(req => `
            <li>
                <strong>${req.requirement || 'Unknown requirement'}</strong>
                ${req.is_mandatory ? '<span class="mandatory-tag">MANDATORY</span>' : ''}
                <br>
                Status: <span class="status-${(req.status || 'unknown').toLowerCase()}">${req.status || 'unknown'}</span>
                • <strong>Exp: ${req.years_of_experience !== null ? req.years_of_experience + 'y' : 'N/A'}</strong> 
                ${req.evidence ? `<span class="evidence">"${req.evidence}"</span>` : ''}
            </li>
        `).join('');

        // 2. Projects (Mapping Agentic fields to your layout)
        const projectRows = (data.project_insights || []).map(p => `
            <li>
                <strong>${p.name || 'Project'}</strong>
                <br>
                <p>${p.description || ''}</p>
            </li>
        `).join('');

        // 3. Domain Experience Table (Mapped to new backend field)
        const domainRows = (data.domain_experience || []).map(d => `
            <tr>
                <td style="padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <strong>${d.domain}</strong>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); font-style: italic;">${d.evidence || ''}</div>
                </td>
                <td style="padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right; vertical-align: top;"><strong>${d.years}y</strong></td>
            </tr>
        `).join('');

        // 4. Scoring Logic (Mapping Agentic fields to your layout)
        const b = {
            mandatory_score: `${data.score}/10`,
            projects_score: `${(data.project_insights || []).length} Projects`,
            depth_score: `${Math.max(...(data.requirements_analysis || []).map(r => r.years_of_experience || 0))}y Peak`,
            logic_explanation: data.scoring_logic || ''
        };

        const candidateId = encodeURIComponent(filename.replace(/\s+/g, '_').toLowerCase());
        card.setAttribute('data-candidate-id', candidateId);

        const key = `candidate_feedback_${candidateId}`;
        const savedData = JSON.parse(localStorage.getItem(key) || '{}');
        const savedNotes = savedData.notes || '';

        const feed = data.feedback || {};
        const bullets = feed.evaluation_bullets || [];
        let bulletsHtml = '';
        if (bullets.length > 0) {
            bulletsHtml = bullets.map(b => `
                <li style="margin-bottom: 8px; line-height: 1.45; color: var(--text-primary); font-size: 0.9rem; text-align: justify;">
                    ${b}
                </li>
            `).join('');
        } else {
            bulletsHtml = `<li style="color: var(--text-secondary); font-size: 0.85rem; font-style: italic;">No evaluation feedback generated.</li>`;
        }

        const feedbackBoxHtml = `
        <div class="agent-feedback-block" style="background: rgba(255, 255, 255, 0.02); border-left: 4px solid var(--accent); padding: 16px 20px; border-radius: 8px; margin-top: 1.2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h4 style="margin: 0 0 12px 0; color: var(--accent); display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 6px;">
                🤖 AI Agent Evaluation
            </h4>
            <ul style="margin: 0; padding-left: 1.1rem; list-style-type: square;">
                ${bulletsHtml}
            </ul>
        </div>`;

        card.innerHTML = `
            <div class="candidate-header">
                <div class="candidate-info">
                    <h2>Candidate Analysis</h2>
                    <span class="filename">${filename}</span>
                </div>
                <div class="candidate-score">
                    <span class="val">${data.score}</span><span class="total">/10</span>
                </div>
            </div>
            <div class="candidate-body">
                <div class="candidate-summary">
                    <h4>Executive Summary</h4>
                    <p>${data.summary || 'Summary not available.'}</p>
                    <div class="scoring-logic">
                        <strong>Scoring Breakdown:</strong>
                        <div class="breakdown-pills">
                            <span class="pill">Mandatory: ${b.mandatory_score}</span>
                            <span class="pill">Projects: ${b.projects_score}</span>
                            <span class="pill">Depth: ${b.depth_score}</span>
                        </div>
                        <p>${b.logic_explanation}</p>
                    </div>
                    
                    ${feedbackBoxHtml}

                    <div class="domain-expertise" style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                        <h4>📊 Domain Expertise</h4>
                        <table style="width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-secondary);">
                            ${domainRows || '<tr><td>No data</td></tr>'}
                        </table>
                    </div>
                </div>
                <div class="candidate-details">
                    <h4>📋 Requirements Check</h4>
                    <ul>${reqRows}</ul>
                </div>
                <div class="candidate-details">
                    <h4>🚀 Relevant Projects</h4>
                    <ul>${projectRows}</ul>
                </div>
            </div>
        `;

        resultsGrid.appendChild(card);
    }

    function addErrorCard(error, filename) {
        const card = document.createElement('div');
        card.className = 'candidate-card glass';
        card.style.borderColor = '#ef4444';
        card.innerHTML = `
            <div class="candidate-header">
                <div class="candidate-info">
                    <h2 style="color: #ef4444">Error analyzing candidate</h2>
                    <span class="filename">${filename}</span>
                </div>
            </div>
            <div class="candidate-body">
                <p>${error}</p>
            </div>
        `;
        resultsGrid.appendChild(card);
    }
    validateForm();
});
