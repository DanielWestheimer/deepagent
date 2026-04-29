        const currentThreadId = crypto.randomUUID();
        const chatWindow = document.getElementById('chat-window');
        const inputField = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function handleEnter(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const text = inputField.value.trim();
            if (!text) return;

            // 1. Add user message to chat window
            addMessageToDOM(text, 'user');
            inputField.value = '';
            
            // 2. Disable input field and show loading message
            inputField.disabled = true;
            sendBtn.disabled = true;
            const typingId = addMessageToDOM('Thinking and executing...', 'agent');
            try {
                // Send the request
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, thread_id: currentThreadId })
                });
                
                // Prepare to read data stream (Streaming)
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                
                const msgDiv = document.getElementById(typingId);
                msgDiv.innerHTML = ""; // Clear initial loading text
                
                // Create two boxes: one for thoughts (small at top) and one for final answer
                const thinkingBox = document.createElement('div');
                thinkingBox.style.fontSize = "0.85em";
                thinkingBox.style.color = "#a6adc8";
                thinkingBox.style.marginBottom = "10px";
                thinkingBox.style.fontFamily = "monospace";
                msgDiv.appendChild(thinkingBox);
                
                const finalAnswerBox = document.createElement('div');
                msgDiv.appendChild(finalAnswerBox);

                // Read data from server live
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n\n'); // Break down the packets sent by server
                    
                    for (let line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.type === 'thinking') {
                                // Print the thought/tool
                                thinkingBox.innerHTML += `<div>${data.content}</div>`;
                                chatWindow.scrollTop = chatWindow.scrollHeight;
                            } 
                            else if (data.type === 'final') {
                                // Print the final answer
                                finalAnswerBox.innerText = data.content;
                                chatWindow.scrollTop = chatWindow.scrollHeight;
                            }
                            else if (data.type === 'error') {
                                finalAnswerBox.innerText = "❌ Error: " + data.content;
                            }
                        }
                    }
                }
            }catch (error) {
                document.getElementById(typingId).innerText = "❌ Communication error. Server not responding.";
            } finally {
                // 5. Release the lock and return focus to input field
                inputField.disabled = false;
                sendBtn.disabled = false;
                inputField.focus();
            }
        }

        function addMessageToDOM(text, sender) {
            const wrapper = document.createElement('div');
            wrapper.className = `msg-wrapper ${sender}-wrapper`;
            
            const msgDiv = document.createElement('div');
            msgDiv.className = `msg ${sender}-msg`;
            msgDiv.innerText = text;
            
            // Create unique ID so we can update the message later
            const id = 'msg-' + Date.now();
            msgDiv.id = id;
            
            wrapper.appendChild(msgDiv);
            chatWindow.appendChild(wrapper);
            
            // Auto-scroll to bottom
            chatWindow.scrollTop = chatWindow.scrollHeight;
            
            return id;
        }
        async function connectToServer() {
            const name = document.getElementById('mcp-name').value.trim();
            const type = document.getElementById('mcp-type').value;
            const cmdOrUrl = document.getElementById('mcp-cmd').value.trim();
            const argsStr = document.getElementById('mcp-args').value.trim();
            const statusDiv = document.getElementById('mcp-status');

            if (!name || !cmdOrUrl) {
                statusDiv.innerText = "⚠️ חסרים פרטים";
                statusDiv.style.color = "#f38ba8";
                return;
            }

            statusDiv.innerText = "מתחבר...";
            statusDiv.style.color = "#f9e2af";

            // בניית אובייקט ההגדרות לפי סוג החיבור
            const payload = { connection_type: type };
            
            if (type === 'stdio') {
                payload.command = cmdOrUrl;
                payload.args = argsStr ? argsStr.split(',').map(s => s.trim()) : [];
            } else {
                payload.url = cmdOrUrl;
            }

            try {
                const response = await fetch(`/mcp/connect?server_name=${encodeURIComponent(name)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.innerText = "✅ מחובר!";
                    statusDiv.style.color = "#a6e3a1";
                    // ניקוי השדות לאחר חיבור מוצלח
                    document.getElementById('mcp-name').value = '';
                    document.getElementById('mcp-cmd').value = '';
                    document.getElementById('mcp-args').value = '';
                    setTimeout(toggleMCP, 1000);
                } else {
                    statusDiv.innerText = "❌ שגיאה";
                    statusDiv.style.color = "#f38ba8";
                }
            } catch (error) {
                statusDiv.innerText = "❌ נפל תקשורת";
                statusDiv.style.color = "#f38ba8";
            }
        }

        function toggleMCP() {
            const panel = document.getElementById('mcp-panel');
            if (panel.style.display === 'none') {
                panel.style.display = 'flex';
            } else {
                panel.style.display = 'none';
            }
        }