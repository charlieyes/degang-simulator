const API_BASE_URL = 'http://localhost:8000';

// DOM Elements - Article Generation
const generateJokeBtn = document.getElementById('generateJokeBtn');
const generateStoryBtn = document.getElementById('generateStoryBtn');
const generatePoemBtn = document.getElementById('generatePoemBtn');
const articlePromptInput = document.getElementById('articlePromptInput');
const generateArticleBtn = document.getElementById('generateArticleBtn');
const articleStatus = document.getElementById('articleStatus');
const step1Section = document.getElementById('step1Section');
const step2Section = document.getElementById('step2Section');
const step3Section = document.getElementById('step3Section');
const articleText = document.getElementById('articleText');
const regenerateArticleBtn = document.getElementById('regenerateArticleBtn');
const copyArticleBtn = document.getElementById('copyArticleBtn');
const articleAudioStatus = document.getElementById('articleAudioStatus');
const articleAudioOutput = document.getElementById('articleAudioOutput');
const articleAudioPlayer = document.getElementById('articleAudioPlayer');
const articleAudioInfo = document.getElementById('articleAudioInfo');
const articleDownloadAudioBtn = document.getElementById('articleDownloadAudioBtn');

// TTS Elements
const ttsTextInput = document.getElementById('ttsTextInput');
const generateTTSBtn = document.getElementById('generateTTSBtn');
const ttsStatus = document.getElementById('ttsStatus');
const ttsOutputSection = document.getElementById('ttsOutputSection');
const ttsAudioPlayer = document.getElementById('ttsAudioPlayer');
const audioInfo = document.getElementById('audioInfo');
const downloadAudioBtn = document.getElementById('downloadAudioBtn');

// Store generated article text for TTS
let generatedArticleText = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Auto-resize textarea
    articlePromptInput.addEventListener('input', () => {
        articlePromptInput.style.height = 'auto';
        articlePromptInput.style.height = Math.min(articlePromptInput.scrollHeight, 120) + 'px';
    });
});

// ============================================================================
// Article Generation Functions
// ============================================================================

// Helper function to generate article with a specific prompt
async function generateArticleWithPrompt(promptText) {
    // Disable buttons and show loading
    generateJokeBtn.disabled = true;
    generateStoryBtn.disabled = true;
    generatePoemBtn.disabled = true;
    generateArticleBtn.disabled = true;
    articleStatus.className = 'article-status loading';
    step2Section.style.display = 'none';
    step3Section.style.display = 'none';
    
    // Start timer
    let seconds = 0;
    const timerInterval = setInterval(() => {
        seconds++;
    }, 1000);
    
    // Status messages that rotate
    let statusIndex = 0;
    const statusMessages = [
        '郭德纲正在思考...',
        '正在组织语言...',
        '正在编段子...',
        '正在打磨笑点...',
        '马上就好，别着急...'
    ];
    
    const updateStatus = () => {
        if (statusIndex < statusMessages.length) {
            articleStatus.textContent = `${statusMessages[statusIndex]} (${seconds}s)`;
            statusIndex++;
        } else {
            articleStatus.textContent = `还在努力创作中... (${seconds}s)`;
        }
    };
    
    updateStatus();
    const statusInterval = setInterval(updateStatus, 1000);
    
    // Use the prompt as-is (it should already include the 200 character limit)
    const finalPrompt = promptText;
    
    try {
        // Call AI API to generate article
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: finalPrompt
            })
        });
        
        // Clear intervals
        clearInterval(timerInterval);
        clearInterval(statusInterval);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const article = data.response || '哎呀，生成失败了...';
        
        // Store generated article
        generatedArticleText = article;
        
        // Show step 2 with generated article
        articleText.textContent = article;
        step1Section.style.display = 'block';
        step2Section.style.display = 'block';
        articleStatus.textContent = `故事讲完了！ (用了 ${seconds}秒)`;
        articleStatus.className = 'article-status success';
        
        // Auto-trigger TTS generation
        await generateAudioFromArticle(article);
        
    } catch (error) {
        // Clear intervals on error
        clearInterval(timerInterval);
        clearInterval(statusInterval);
        
        console.error('Try Luck Error:', error);
        articleStatus.textContent = `哎呀出错了: ${error.message}`;
        articleStatus.className = 'article-status error';
        step2Section.style.display = 'none';
        step3Section.style.display = 'none';
    } finally {
        generateJokeBtn.disabled = false;
        generateStoryBtn.disabled = false;
        generatePoemBtn.disabled = false;
        generateArticleBtn.disabled = false;
    }
}

// Generate Joke
generateJokeBtn.addEventListener('click', async () => {
    await generateArticleWithPrompt('给我讲个笑话。请确保内容在200字以内。');
});

// Generate Story
generateStoryBtn.addEventListener('click', async () => {
    await generateArticleWithPrompt('写个小故事。请确保内容在200字以内。');
});

// Generate Poem - Request real Chinese classical poetry
generatePoemBtn.addEventListener('click', async () => {
    await generateArticleWithPrompt('给我推荐一首中国古诗，并附上简短的赏析。请确保总内容在200字以内。');
});

// Helper function to count Chinese characters
function countChineseChars(text) {
    // Count Chinese characters (CJK Unified Ideographs)
    const chineseRegex = /[\u4e00-\u9fff]/g;
    const matches = text.match(chineseRegex);
    return matches ? matches.length : 0;
}

// Generate article from prompt
generateArticleBtn.addEventListener('click', async () => {
    const prompt = articlePromptInput.value.trim();
    
    if (!prompt) {
        articleStatus.textContent = '先写点啥吧，不然我怎么知道你想听什么？';
        articleStatus.className = 'article-status error';
        return;
    }
    
    // Inject 200 character limit into the prompt
    const finalPrompt = prompt + '。请确保内容在200字以内。';
    
    // Disable buttons and show loading
    generateArticleBtn.disabled = true;
    generateJokeBtn.disabled = true;
    generateStoryBtn.disabled = true;
    generatePoemBtn.disabled = true;
    articleStatus.className = 'article-status loading';
    step2Section.style.display = 'none';
    step3Section.style.display = 'none';
    
    // Start timer
    let seconds = 0;
    const timerInterval = setInterval(() => {
        seconds++;
    }, 1000);
    
    // Status messages that rotate
    let statusIndex = 0;
    const statusMessages = [
        '郭德纲正在思考...',
        '正在组织语言...',
        '正在编段子...',
        '正在打磨笑点...',
        '马上就好，别着急...'
    ];
    
    const updateStatus = () => {
        if (statusIndex < statusMessages.length) {
            articleStatus.textContent = `${statusMessages[statusIndex]} (${seconds}s)`;
            statusIndex++;
        } else {
            articleStatus.textContent = `还在努力创作中... (${seconds}s)`;
        }
    };
    
    updateStatus();
    const statusInterval = setInterval(updateStatus, 1000);
    
    try {
        // Call AI API to generate article
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: finalPrompt
            })
        });
        
        // Clear intervals
        clearInterval(timerInterval);
        clearInterval(statusInterval);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const article = data.response || '生成失败';
        
        // Store generated article
        generatedArticleText = article;
        
        // Show step 2 with generated article
        articleText.textContent = article;
        step2Section.style.display = 'block';
        articleStatus.textContent = `文章生成成功！ (耗时 ${seconds}秒)`;
        articleStatus.className = 'article-status success';
        
        // Auto-trigger TTS generation
        await generateAudioFromArticle(article);
        
    } catch (error) {
        // Clear intervals on error
        clearInterval(timerInterval);
        clearInterval(statusInterval);
        
        console.error('Article Generation Error:', error);
        articleStatus.textContent = `哎呀出错了: ${error.message}`;
        articleStatus.className = 'article-status error';
        step2Section.style.display = 'none';
        step3Section.style.display = 'none';
    } finally {
        generateArticleBtn.disabled = false;
        generateJokeBtn.disabled = false;
        generateStoryBtn.disabled = false;
        generatePoemBtn.disabled = false;
    }
});

// Regenerate article
regenerateArticleBtn.addEventListener('click', () => {
    generateArticleBtn.click();
});

// Copy article text
copyArticleBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(generatedArticleText).then(() => {
        copyArticleBtn.textContent = '复制成功！';
        setTimeout(() => {
            copyArticleBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>复制文本';
        }, 2000);
    });
});

// Generate audio from article (auto-triggered)
async function generateAudioFromArticle(text) {
    // Show step 3
    step3Section.style.display = 'block';
    articleAudioStatus.className = 'article-audio-status loading';
    articleAudioOutput.style.display = 'none';
    
    // Start timer
    let seconds = 0;
    const timerInterval = setInterval(() => {
        seconds++;
    }, 1000);
    
    // Status update function
    let statusIndex = 0;
    const statusMessages = [
        'AI正在准备声音...',
        '正在理解文字...',
        '正在调整语调...',
        '正在合成声音...',
        '正在打磨细节...',
        '马上就能听了...'
    ];
    
    const updateStatus = () => {
        if (statusIndex < statusMessages.length) {
            articleAudioStatus.textContent = `${statusMessages[statusIndex]} (${seconds}s)`;
            statusIndex++;
        } else {
            articleAudioStatus.textContent = `还在努力合成中... (${seconds}s)`;
        }
    };
    
    updateStatus();
    const statusInterval = setInterval(() => {
        updateStatus();
    }, 1000);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/tts/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        // Clear intervals once we get response
        clearInterval(timerInterval);
        clearInterval(statusInterval);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Set audio source
            articleAudioPlayer.src = `${API_BASE_URL}${data.audio_url}`;
            
            // Update audio info
            articleAudioInfo.innerHTML = `
                <strong>文本:</strong> ${data.text.substring(0, 100)}${data.text.length > 100 ? '...' : ''}<br>
                <strong>时长:</strong> ${data.duration} 秒<br>
                <strong>采样率:</strong> ${data.sample_rate} Hz
            `;
            
            // Set download link
            articleDownloadAudioBtn.href = `${API_BASE_URL}${data.audio_url}`;
            articleDownloadAudioBtn.download = data.filename;
            
            // Show audio output
            articleAudioOutput.style.display = 'block';
            articleAudioStatus.textContent = `声音合成完成！ ✓ (用了 ${seconds}秒)`;
            articleAudioStatus.className = 'article-audio-status success';
            
            // Play audio automatically
            articleAudioPlayer.play().catch(err => {
                console.log('Auto-play prevented:', err);
            });
        } else {
            throw new Error('哎呀，音频生成失败了');
        }
        
    } catch (error) {
        clearInterval(timerInterval);
        clearInterval(statusInterval);
        console.error('TTS Error:', error);
        articleAudioStatus.textContent = `出错了: ${error.message}`;
        articleAudioStatus.className = 'article-audio-status error';
        articleAudioOutput.style.display = 'none';
    }
}


// ============================================================================
// TTS Functions
// ============================================================================

// Switch between tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    if (tabName === 'article') {
        document.getElementById('articleTabBtn').classList.add('active');
    } else if (tabName === 'tts') {
        document.getElementById('ttsTabBtn').classList.add('active');
    }
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    if (tabName === 'article') {
        document.getElementById('articleTab').classList.add('active');
    } else if (tabName === 'tts') {
        document.getElementById('ttsTab').classList.add('active');
    }
}

// Generate TTS audio
generateTTSBtn.addEventListener('click', async () => {
    const text = ttsTextInput.value.trim();
    
    if (!text) {
        ttsStatus.textContent = '先写点文字吧，不然我怎么读？';
        ttsStatus.className = 'tts-status error';
        return;
    }
    
    // Check if text exceeds 200 Chinese characters
    const chineseCharCount = countChineseChars(text);
    if (chineseCharCount > 200) {
        ttsStatus.textContent = `文字太长了！当前有${chineseCharCount}个中文字符，请缩短到200字以内`;
        ttsStatus.className = 'tts-status error';
        return;
    }
    
    // Disable button and show loading
    generateTTSBtn.disabled = true;
    ttsStatus.className = 'tts-status loading';
    ttsOutputSection.style.display = 'none';
    
    // Status update function
    let statusIndex = 0;
    const statusMessages = [
        'AI正在准备声音...',
        '正在理解文字...',
        '正在调整语调...',
        '正在合成声音...',
        '正在打磨细节...',
        '马上就能听了...'
    ];
    
    const updateStatus = () => {
        if (statusIndex < statusMessages.length) {
            ttsStatus.textContent = statusMessages[statusIndex];
            statusIndex++;
        }
    };
    
    // Start with first status
    updateStatus();
    
    // Update status periodically to show progress
    const statusInterval = setInterval(() => {
        updateStatus();
    }, 2000); // Update every 2 seconds
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/tts/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        // Clear status interval once we get response
        clearInterval(statusInterval);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Set audio source
            ttsAudioPlayer.src = `${API_BASE_URL}${data.audio_url}`;
            
            // Update audio info
            audioInfo.innerHTML = `
                <strong>Text:</strong> ${data.text}<br>
                <strong>Duration:</strong> ${data.duration} seconds<br>
                <strong>Sample Rate:</strong> ${data.sample_rate} Hz
            `;
            
            // Set download link
            downloadAudioBtn.href = `${API_BASE_URL}${data.audio_url}`;
            downloadAudioBtn.download = data.filename;
            
            // Show output section
            ttsOutputSection.style.display = 'block';
            
            // Update status
            ttsStatus.textContent = '声音合成完成！ ✓';
            ttsStatus.className = 'tts-status success';
            
            // Play audio automatically
            ttsAudioPlayer.play().catch(err => {
                console.log('Auto-play prevented:', err);
            });
        } else {
            throw new Error('哎呀，音频生成失败了');
        }
        
    } catch (error) {
        // Clear status interval on error
        clearInterval(statusInterval);
        
        console.error('TTS Error:', error);
        ttsStatus.textContent = `出错了: ${error.message}`;
        ttsStatus.className = 'tts-status error';
        ttsOutputSection.style.display = 'none';
    } finally {
        generateTTSBtn.disabled = false;
    }
});

// Handle Enter key in TTS textarea (Ctrl+Enter to submit)
ttsTextInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        generateTTSBtn.click();
    }
});
