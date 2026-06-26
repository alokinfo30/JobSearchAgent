document.addEventListener('DOMContentLoaded', function() {
    const searchBtn = document.getElementById('searchBtn');
    const roleInput = document.getElementById('role');
    const locationInput = document.getElementById('location');
    const resultsSection = document.getElementById('results');
    const jobList = document.getElementById('jobList');
    const processing = document.getElementById('processing');
    const jobDetails = document.getElementById('jobDetails');
    const jobContent = document.getElementById('jobContent');
    const processingStatus = document.getElementById('processingStatus');

    // Stats elements
    const jobsFoundEl = document.getElementById('jobsFound');
    const appsProcessedEl = document.getElementById('appsProcessed');
    const lastRunEl = document.getElementById('lastRun');
    const intervalDisplay = document.getElementById('intervalDisplay');

    // Load last run status
    async function loadStatus() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            if (data.status === 'healthy') {
                // Update interval
                intervalDisplay.textContent = '24';
            }
        } catch (error) {
            console.error('Error loading status:', error);
        }
    }

    // Search jobs
    searchBtn.addEventListener('click', async function() {
        const role = roleInput.value.trim();
        const location = locationInput.value.trim();

        if (!role) {
            alert('Please enter a role to search for');
            return;
        }

        // Show processing
        processing.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        jobDetails.classList.add('hidden');
        searchBtn.disabled = true;
        searchBtn.textContent = 'Searching...';
        updateAgentStatus('searching', 'Searching for jobs...');

        try {
            // Search for jobs
            const searchResponse = await fetch('/api/search_jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ role, location })
            });

            const searchData = await searchResponse.json();

            if (searchResponse.ok && searchData.status === 'success') {
                const jobs = searchData.jobs;
                jobsFoundEl.textContent = jobs.length;
                displayJobs(jobs);

                // Process first job automatically
                if (jobs.length > 0) {
                    updateAgentStatus('customizing', 'Customizing resume for first job...');
                    await processJob(jobs[0]);
                }

                resultsSection.classList.remove('hidden');
                searchBtn.textContent = '✅ Search Complete';
            } else {
                alert('Error searching jobs: ' + (searchData.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error searching jobs. Please try again.');
        } finally {
            processing.classList.add('hidden');
            searchBtn.disabled = false;
            searchBtn.textContent = '🔍 Search Jobs Now';
            updateAgentStatus('idle', '');
        }
    });

    async function processJob(job) {
        updateAgentStatus('customizing', `Processing ${job.title} at ${job.company}`);

        try {
            // In a real implementation, you would load the actual resume
            const resumeContent = await loadResume();

            const processResponse = await fetch('/api/process_job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    job: job,
                    resume_content: resumeContent
                })
            });

            const processData = await processResponse.json();

            if (processResponse.ok && processData.status === 'success') {
                appsProcessedEl.textContent = parseInt(appsProcessedEl.textContent || 0) + 1;
                lastRunEl.textContent = new Date().toLocaleString();

                // Display results
                displayJobDetails(job, processData.result);
                updateAgentStatus('complete', `Completed ${job.title} at ${job.company}`);
            } else {
                console.error('Error processing job:', processData);
                updateAgentStatus('error', `Error: ${processData.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error processing job:', error);
            updateAgentStatus('error', `Error: ${error.message}`);
        }
    }

    function displayJobs(jobs) {
        jobList.innerHTML = '';
        
        if (jobs.length === 0) {
            jobList.innerHTML = '<p>No jobs found matching your criteria.</p>';
            return;
        }

        jobs.forEach((job, index) => {
            const item = document.createElement('div');
            item.className = 'job-item';
            item.innerHTML = `
                <h3>${job.title}</h3>
                <div class="company">${job.company}</div>
                <div class="location">📍 ${job.location}</div>
                <div style="margin-top: 10px; font-size: 0.9rem; color: #666;">
                    ${job.description ? job.description.substring(0, 100) + '...' : ''}
                </div>
            `;
            item.addEventListener('click', () => {
                if (window.confirm(`Process application for ${job.title} at ${job.company}?`)) {
                    processJob(job);
                }
            });
            jobList.appendChild(item);
        });
    }

    function displayJobDetails(job, result) {
        jobDetails.classList.remove('hidden');
        
        let html = `
            <h3>${job.title} at ${job.company}</h3>
            <p><strong>Location:</strong> ${job.location}</p>
            <p><strong>Description:</strong> ${job.description || 'N/A'}</p>
            <hr>
            <h4>Customized Resume</h4>
            <pre>${result.customized_resume || 'Not available'}</pre>
            <hr>
            <h4>Email Draft</h4>
            <pre>${result.email_draft || 'Not available'}</pre>
        `;
        
        jobContent.innerHTML = html;
        
        // Scroll to details
        jobDetails.scrollIntoView({ behavior: 'smooth' });
    }

    function updateAgentStatus(status, message) {
        const statusMap = {
            'idle': { agent1: '⏳ Job Searcher: Idle', agent2: '⏳ Resume Customizer: Idle', agent3: '⏳ Email Drafter: Idle' },
            'searching': { agent1: '🔍 Job Searcher: Searching...', agent2: '⏳ Resume Customizer: Waiting', agent3: '⏳ Email Drafter: Waiting' },
            'customizing': { agent1: '✅ Job Searcher: Complete', agent2: '✏️ Resume Customizer: Customizing...', agent3: '⏳ Email Drafter: Waiting' },
            'email': { agent1: '✅ Job Searcher: Complete', agent2: '✅ Resume Customizer: Complete', agent3: '✉️ Email Drafter: Drafting...' },
            'complete': { agent1: '✅ Job Searcher: Complete', agent2: '✅ Resume Customizer: Complete', agent3: '✅ Email Drafter: Complete' },
            'error': { agent1: '❌ Job Searcher: Error', agent2: '❌ Resume Customizer: Error', agent3: '❌ Email Drafter: Error' }
        };

        const statuses = statusMap[status] || statusMap.idle;
        document.getElementById('agent1').textContent = statuses.agent1;
        document.getElementById('agent2').textContent = statuses.agent2;
        document.getElementById('agent3').textContent = statuses.agent3;
        
        if (message) {
            processingStatus.textContent = message;
        }
    }

    async function loadResume() {
        // In a real implementation, this would load from file or database
        return `# [Your Name]
## Contact Information
- **Email**: your.email@example.com
- **Phone**: (123) 456-7890
- **Location**: Remote/Anywhere

## Professional Summary
Experienced software developer with 5+ years of experience in building scalable applications.

## Technical Skills
- **Programming Languages**: Python, JavaScript, Java
- **Frameworks**: Django, Flask, React
- **Tools**: Git, Docker, AWS`;
    }

    // Initialize
    loadStatus();
    updateAgentStatus('idle', '');
    console.log('🤖 Automated Job Search Agent loaded successfully!');
});