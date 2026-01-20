/**
 * Wagtail Context Search Assistant Widget
 */

(function() {
    'use strict';

    class RAGAssistant {
        constructor(config) {
            this.config = config || {};
            this.apiUrl = this.config.apiUrl || '/rag/query/';
            this.mode = this.config.mode || 'both'; // 'chat', 'search', 'both'
            this.position = this.config.position || 'bottom-right';
            this.theme = this.config.theme || 'light';
            this.messages = [];
            this.isOpen = false;
            this.isLoading = false;
            
            this.init();
        }

        init() {
            this.createWidget();
            this.attachEvents();
        }

        createWidget() {
            // Create container
            const container = document.createElement('div');
            container.className = `rag-assistant-container rag-assistant-${this.position}`;
            container.id = 'rag-assistant-container';

            // Create button
            const button = document.createElement('button');
            button.className = 'rag-assistant-button';
            button.setAttribute('aria-label', 'Open assistant');
            button.innerHTML = '💬';
            this.button = button;

            // Create widget
            const widget = document.createElement('div');
            widget.className = `rag-assistant-widget rag-assistant-theme-${this.theme}`;
            if (this.mode === 'search') {
                widget.classList.add('rag-assistant-search-mode');
            }
            this.widget = widget;

            // Create header
            const header = document.createElement('div');
            header.className = 'rag-assistant-header';
            header.innerHTML = `
                <h3>Site Assistant</h3>
                <button class="rag-assistant-close" aria-label="Close">×</button>
            `;

            // Create messages container
            const messages = document.createElement('div');
            messages.className = 'rag-assistant-messages';
            this.messagesContainer = messages;

            // Create input container
            const inputContainer = document.createElement('div');
            inputContainer.className = 'rag-assistant-input-container';
            const inputWrapper = document.createElement('div');
            inputWrapper.className = 'rag-assistant-input-wrapper';
            
            const input = document.createElement('textarea');
            input.className = 'rag-assistant-input';
            input.placeholder = this.mode === 'search' ? 'Search the site...' : 'Ask a question...';
            input.setAttribute('rows', '1');
            this.input = input;

            const sendButton = document.createElement('button');
            sendButton.className = 'rag-assistant-send';
            sendButton.setAttribute('aria-label', 'Send');
            sendButton.innerHTML = '➤';
            this.sendButton = sendButton;

            inputWrapper.appendChild(input);
            inputWrapper.appendChild(sendButton);
            inputContainer.appendChild(inputWrapper);

            // Assemble widget
            widget.appendChild(header);
            widget.appendChild(messages);
            widget.appendChild(inputContainer);

            // Assemble container
            container.appendChild(button);
            container.appendChild(widget);

            // Add to page
            document.body.appendChild(container);
        }

        attachEvents() {
            // Toggle widget
            this.button.addEventListener('click', () => {
                this.toggle();
            });

            // Close button
            this.widget.querySelector('.rag-assistant-close').addEventListener('click', () => {
                this.close();
            });

            // Send button
            this.sendButton.addEventListener('click', () => {
                this.sendMessage();
            });

            // Enter key (Shift+Enter for new line)
            this.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            this.input.addEventListener('input', () => {
                this.input.style.height = 'auto';
                this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
            });
        }

        toggle() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }

        open() {
            this.isOpen = true;
            this.widget.classList.add('rag-assistant-widget-open');
            this.input.focus();
        }

        close() {
            this.isOpen = false;
            this.widget.classList.remove('rag-assistant-widget-open');
        }

        async sendMessage() {
            const query = this.input.value.trim();
            if (!query || this.isLoading) {
                return;
            }

            // Add user message
            this.addMessage('user', query);
            this.input.value = '';
            this.input.style.height = 'auto';

            // Show loading
            this.setLoading(true);

            try {
                // Get CSRF token from cookies if available
                const getCookie = (name) => {
                    const value = `; ${document.cookie}`;
                    const parts = value.split(`; ${name}=`);
                    if (parts.length === 2) return parts.pop().split(';').shift();
                    return null;
                };
                
                const csrftoken = getCookie('csrftoken');
                const headers = {
                    'Content-Type': 'application/json',
                };
                
                // Add CSRF token if available (though view should be exempt)
                if (csrftoken) {
                    headers['X-CSRFToken'] = csrftoken;
                }
                
                const response = await fetch(this.apiUrl, {
                    method: 'POST',
                    headers: headers,
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        query: query,
                        stream: false,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                // Add assistant message
                this.addMessage('assistant', data.answer, data.sources);
            } catch (error) {
                console.error('Error:', error);
                this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            } finally {
                this.setLoading(false);
            }
        }

        addMessage(type, content, sources = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `rag-assistant-message rag-assistant-message-${type}`;

            const bubble = document.createElement('div');
            bubble.className = 'rag-assistant-message-bubble';
            bubble.textContent = content;
            messageDiv.appendChild(bubble);

            // Add sources if available
            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'rag-assistant-sources';
                sourcesDiv.innerHTML = 'Sources: ' + sources.map(s => {
                    if (s.url) {
                        return `<a href="${s.url}" target="_blank">${s.title}</a>`;
                    }
                    return s.title;
                }).join(', ');
                messageDiv.appendChild(sourcesDiv);
            }

            this.messagesContainer.appendChild(messageDiv);
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

            this.messages.push({ type, content, sources });
        }

        setLoading(loading) {
            this.isLoading = loading;
            this.sendButton.disabled = loading;

            if (loading) {
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'rag-assistant-loading';
                loadingDiv.innerHTML = `
                    <div class="rag-assistant-loading-dot"></div>
                    <div class="rag-assistant-loading-dot"></div>
                    <div class="rag-assistant-loading-dot"></div>
                `;
                this.messagesContainer.appendChild(loadingDiv);
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            } else {
                const loading = this.messagesContainer.querySelector('.rag-assistant-loading');
                if (loading) {
                    loading.remove();
                }
            }
        }
    }

    // Auto-initialize if config is available
    if (typeof window.ragAssistantConfig !== 'undefined') {
        window.ragAssistant = new RAGAssistant(window.ragAssistantConfig);
    }

    // Export for manual initialization
    window.RAGAssistant = RAGAssistant;
})();
