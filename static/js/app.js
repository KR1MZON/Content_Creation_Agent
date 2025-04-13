document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
});

/**
 * Initialize the application
 */
function initApp() {
    // Set up page navigation
    setupNavigation();
    
    // Set up content source tabs
    setupContentSourceTabs();
    
    // Set up event listeners for buttons
    setupEventListeners();
}

/**
 * Set up page navigation
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const pages = document.querySelectorAll('.page');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and pages
            navLinks.forEach(l => l.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show the corresponding page
            const pageId = this.getAttribute('data-page');
            document.getElementById(`${pageId}-page`).classList.add('active');
        });
    });
}

/**
 * Set up content source tabs
 */
function setupContentSourceTabs() {
    const sourceTabs = document.querySelectorAll('#content-source-tabs .nav-link');
    const sourceInputs = document.querySelectorAll('.source-input');
    
    sourceTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs and inputs
            sourceTabs.forEach(t => t.classList.remove('active'));
            sourceInputs.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show the corresponding input
            const sourceId = this.getAttribute('data-source');
            document.getElementById(`${sourceId}-source`).classList.add('active');
        });
    });
}

/**
 * Set up event listeners for buttons
 */
function setupEventListeners() {
    // Generate button
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateContent);
    }
    
    // Copy button
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyContent);
    }
    
    // Edit button
    const editBtn = document.getElementById('edit-btn');
    if (editBtn) {
        editBtn.addEventListener('click', editContent);
    }
    
    // Regenerate button
    const regenerateBtn = document.getElementById('regenerate-btn');
    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', regenerateContent);
    }
    
    // Publish button
    const publishBtn = document.getElementById('publish-btn');
    if (publishBtn) {
        publishBtn.addEventListener('click', showPublishModal);
    }
    
    // Schedule button
    const scheduleBtn = document.getElementById('schedule-btn');
    if (scheduleBtn) {
        scheduleBtn.addEventListener('click', showScheduleModal);
    }
    
    // Confirm publish button
    const confirmPublishBtn = document.getElementById('confirm-publish-btn');
    if (confirmPublishBtn) {
        confirmPublishBtn.addEventListener('click', publishContent);
    }
    
    // Confirm schedule button
    const confirmScheduleBtn = document.getElementById('confirm-schedule-btn');
    if (confirmScheduleBtn) {
        confirmScheduleBtn.addEventListener('click', scheduleContent);
    }
    
    // Save schedule button (on schedule page)
    const saveScheduleBtn = document.getElementById('save-schedule-btn');
    if (saveScheduleBtn) {
        saveScheduleBtn.addEventListener('click', scheduleContentFromPage);
    }
}

/**
 * Generate content based on the selected source
 */
async function generateContent() {
    // Show loading state
    const generateBtn = document.getElementById('generate-btn');
    const originalText = generateBtn.textContent;
    generateBtn.textContent = 'Generating...';
    generateBtn.disabled = true;
    
    try {
        // Get the active source
        const activeTab = document.querySelector('#content-source-tabs .nav-link.active');
        const sourceType = activeTab.getAttribute('data-source');
        
        // Get the source data
        let sourceData;
        switch (sourceType) {
            case 'text':
                sourceData = document.getElementById('text-input').value;
                break;
            case 'bullets':
                sourceData = document.getElementById('bullets-input').value;
                break;
            case 'url':
                sourceData = document.getElementById('url-input').value;
                break;
            case 'file':
                // Handle file upload
                const fileInput = document.getElementById('file-input');
                if (fileInput.files.length > 0) {
                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);
                    
                    // Get the tone
                    const tone = document.getElementById('tone-select').value;
                    formData.append('tone', tone);
                    
                    // Send the file to the server
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to upload file');
                    }
                    
                    const data = await response.json();
                    displayGeneratedContent(data.content);
                    return;
                } else {
                    alert('Please select a file to upload');
                    return;
                }
            default:
                alert('Please select a valid source type');
                return;
        }
        
        // Get the tone
        const tone = document.getElementById('tone-select').value;
        
        // Send the request to the server
        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_type: sourceType,
                source_data: sourceData,
                tone: tone
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate content');
        }
        
        const data = await response.json();
        displayGeneratedContent(data.content);
    } catch (error) {
        console.error('Error generating content:', error);
        alert('Error generating content: ' + error.message);
    } finally {
        // Reset button state
        generateBtn.textContent = originalText;
        generateBtn.disabled = false;
    }
}

/**
 * Display the generated content
 */
function displayGeneratedContent(content) {
    // Show the generated content card
    const generatedContent = document.getElementById('generated-content');
    generatedContent.classList.remove('d-none');
    
    // Set the content
    const contentDisplay = document.getElementById('content-display');
    contentDisplay.textContent = content;
    
    // Scroll to the generated content
    generatedContent.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Copy the generated content to clipboard
 */
function copyContent() {
    const contentDisplay = document.getElementById('content-display');
    const content = contentDisplay.textContent;
    
    navigator.clipboard.writeText(content)
        .then(() => {
            // Show success message
            const copyBtn = document.getElementById('copy-btn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            
            // Reset button text after 2 seconds
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Error copying content:', err);
            alert('Failed to copy content');
        });
}

/**
 * Edit the generated content
 */
function editContent() {
    const contentDisplay = document.getElementById('content-display');
    const content = contentDisplay.textContent;
    
    // Create a textarea for editing
    contentDisplay.innerHTML = '';
    const textarea = document.createElement('textarea');
    textarea.className = 'form-control';
    textarea.rows = 6;
    textarea.value = content;
    contentDisplay.appendChild(textarea);
    
    // Create save button
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary mt-2';
    saveBtn.textContent = 'Save Changes';
    saveBtn.addEventListener('click', function() {
        const newContent = textarea.value;
        contentDisplay.innerHTML = '';
        contentDisplay.textContent = newContent;
    });
    contentDisplay.appendChild(saveBtn);
    
    // Focus the textarea
    textarea.focus();
}

/**
 * Regenerate the content
 */
function regenerateContent() {
    // Simply call generateContent again
    generateContent();
}

/**
 * Show the publish modal
 */
function showPublishModal() {
    // Show the modal
    const publishModal = new bootstrap.Modal(document.getElementById('publish-modal'));
    publishModal.show();
    
    // TODO: Fetch LinkedIn accounts and populate the dropdown
}

/**
 * Show the schedule modal
 */
function showScheduleModal() {
    // Show the modal
    const scheduleModal = new bootstrap.Modal(document.getElementById('schedule-modal'));
    scheduleModal.show();
    
    // Set default date to tomorrow at 9 AM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    
    const dateTimeInput = document.getElementById('modal-schedule-datetime');
    dateTimeInput.value = tomorrow.toISOString().slice(0, 16);
    
    // TODO: Fetch LinkedIn accounts and populate the dropdown
}

/**
 * Publish content to LinkedIn
 */
async function publishContent() {
    // Get the content
    const content = document.getElementById('content-display').textContent;
    
    // Get the selected LinkedIn account
    const accountSelect = document.getElementById('modal-publish-account');
    const accountId = accountSelect.value;
    
    if (!accountId) {
        alert('Please select a LinkedIn account');
        return;
    }
    
    try {
        // Show loading state
        const publishBtn = document.getElementById('confirm-publish-btn');
        const originalText = publishBtn.textContent;
        publishBtn.textContent = 'Publishing...';
        publishBtn.disabled = true;
        
        // TODO: Get actual account details from the server
        const accountDetails = {
            access_token: 'dummy_token',
            refresh_token: 'dummy_refresh_token',
            token_expires_at: new Date().toISOString()
        };
        
        // Send the request to the server
        const response = await fetch('/api/publish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                access_token: accountDetails.access_token,
                refresh_token: accountDetails.refresh_token,
                token_expires_at: accountDetails.token_expires_at
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to publish content');
        }
        
        const data = await response.json();
        
        // Close the modal
        const publishModal = bootstrap.Modal.getInstance(document.getElementById('publish-modal'));
        publishModal.hide();
        
        // Show success message
        alert('Post published successfully!');
        
    } catch (error) {
        console.error('Error publishing content:', error);
        alert('Error publishing content: ' + error.message);
    } finally {
        // Reset button state
        const publishBtn = document.getElementById('confirm-publish-btn');
        publishBtn.textContent = 'Publish';
        publishBtn.disabled = false;
    }
}

/**
 * Schedule content from the modal
 */
async function scheduleContent() {
    // Get the content
    const content = document.getElementById('content-display').textContent;
    
    // Get the selected LinkedIn account
    const accountSelect = document.getElementById('modal-linkedin-account');
    const accountId = accountSelect.value;
    
    // Get the scheduled time
    const scheduledTime = document.getElementById('modal-schedule-datetime').value;
    
    if (!accountId) {
        alert('Please select a LinkedIn account');
        return;
    }
    
    if (!scheduledTime) {
        alert('Please select a date and time');
        return;
    }
    
    try {
        // Show loading state
        const scheduleBtn = document.getElementById('confirm-schedule-btn');
        const originalText = scheduleBtn.textContent;
        scheduleBtn.textContent = 'Scheduling...';
        scheduleBtn.disabled = true;
        
        // Send the request to the server
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                scheduled_time: scheduledTime,
                linkedin_account: accountId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to schedule post');
        }
        
        const data = await response.json();
        
        // Close the modal
        const scheduleModal = bootstrap.Modal.getInstance(document.getElementById('schedule-modal'));
        scheduleModal.hide();
        
        // Show success message
        alert('Post scheduled successfully!');
        
        // Refresh upcoming posts if on schedule page
        if (document.getElementById('schedule-page').classList.contains('active')) {
            // TODO: Implement fetchUpcomingPosts()
        }
        
    } catch (error) {
        console.error('Error scheduling post:', error);
        alert('Error scheduling post: ' + error.message);
    } finally {
        // Reset button state
        const scheduleBtn = document.getElementById('confirm-schedule-btn');
        scheduleBtn.textContent = 'Schedule';
        scheduleBtn.disabled = false;
    }
}

/**
 * Schedule content from the schedule page
 */
async function scheduleContentFromPage() {
    // Get the content
    const content = document.getElementById('scheduled-content').value;
    
    // Get the selected LinkedIn account
    const accountSelect = document.getElementById('linkedin-account');
    const accountId = accountSelect.value;
    
    // Get the scheduled time
    const scheduledTime = document.getElementById('schedule-datetime').value;
    
    if (!content) {
        alert('Please enter content for your post');
        return;
    }
    
    if (!accountId) {
        alert('Please select a LinkedIn account');
        return;
    }
    
    if (!scheduledTime) {
        alert('Please select a date and time');
        return;
    }
    
    try {
        // Show loading state
        const scheduleBtn = document.getElementById('save-schedule-btn');
        const originalText = scheduleBtn.textContent;
        scheduleBtn.textContent = 'Scheduling...';
        scheduleBtn.disabled = true;
        
        // Send the request to the server
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                scheduled_time: scheduledTime,
                linkedin_account: accountId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to schedule post');
        }
        
        const data = await response.json();
        
        // Clear the form
        document.getElementById('scheduled-content').value = '';
        document.getElementById('schedule-datetime').value = '';
        
        // Show success message
        alert('Post scheduled successfully!');
        
        // Refresh upcoming posts
        // TODO: Implement fetchUpcomingPosts()
        
    } catch (error) {
        console.error('Error scheduling post:', error);
        alert('Error scheduling post: ' + error.message);
    } finally {
        // Reset button state
        const scheduleBtn = document.getElementById('save-schedule-btn');
        scheduleBtn.textContent = 'Schedule Post';
        scheduleBtn.disabled = false;
    }
}

/**
 * Fetch upcoming posts
 */
async function fetchUpcomingPosts() {
    try {
        // Send the request to the server
        const response = await fetch('/api/upcoming-posts');
        
        if (!response.ok) {
            throw new Error('Failed to fetch upcoming posts');
        }
        
        const data = await response.json();
        
        // Update the UI
        const upcomingPostsContainer = document.getElementById('upcoming-posts');
        upcomingPostsContainer.innerHTML = '';
        
        if (data.posts && data.posts.length > 0) {
            data.posts.forEach(post => {
                const postElement = document.createElement('div');
                postElement.className = 'upcoming-post p-2 mb-2 bg-light';
                postElement.innerHTML = `
                    <div class="post-time">${new Date(post.scheduled_time).toLocaleString()}</div>
                    <div class="post-content">${post.content}</div>
                `;
                upcomingPostsContainer.appendChild(postElement);
            });
        } else {
            upcomingPostsContainer.innerHTML = '<div class="text-center text-muted py-3">No scheduled posts</div>';
        }
        
    } catch (error) {
        console.error('Error fetching upcoming posts:', error);
    }
}

/**
 * Fetch dashboard data
 */
async function fetchDashboardData() {
    try {
        // Send the request to the server
        const response = await fetch('/api/dashboard');
        
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data');
        }
        
        const data = await response.json();
        
        // Update the UI
        // TODO: Update dashboard stats and recent posts table
        
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}