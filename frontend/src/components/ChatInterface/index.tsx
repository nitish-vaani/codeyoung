import React, { useState, useEffect, useRef } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';

interface ChatMessage {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  sender: string;
}

interface ChatInterfaceProps {
  onClose?: () => void;
  selectedAgent?: {
    model_id: string;
    model_name: string;
  };
  customerName?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onClose, selectedAgent, customerName }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [room, setRoom] = useState<Room | null>(null);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useRef<Toast>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Use useRef for accumulation to avoid stale closure issues
  const accumulatorRef = useRef<string>('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const showToast = (severity: 'success' | 'info' | 'warn' | 'error', summary: string, detail?: string) => {
    toast.current?.show({ severity, summary, detail, life: 3000 });
  };

  const addMessage = (type: 'user' | 'agent' | 'system', content: string, sender: string = '') => {
    console.log('🔵 Adding message:', type, content.substring(0, 50) + '...');
    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      content,
      timestamp: new Date(),
      sender: sender || type
    };
    setMessages(prev => {
      const updated = [...prev, newMessage];
      console.log('🔵 Messages now:', updated.length);
      return updated;
    });
  };

  const connectToChat = async () => {
    try {
      setIsConnecting(true);
      setConnectionError(null);
      
      const user_id = localStorage.getItem("fullName");
      const user_name = localStorage.getItem("Name") || "Chat User";
      
      if (!user_id) {
        throw new Error("Please login first");
      }

      console.log('Starting chat connection for user:', user_name);

      // Step 1: Create chat session
      const chatResponse = await fetch('https://codeyoung-bk.vaaniresearch.com/api/trigger-chat/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          user_id: user_id,
          agent_id: selectedAgent?.model_id || "3", 
          name: customerName || user_name,
          agent_name: selectedAgent?.model_name || "Codeyoung Agent"
        })
      });

      if (!chatResponse.ok) {
        const errorText = await chatResponse.text();
        console.error('Chat creation failed:', errorText);
        throw new Error(`Failed to create chat session: ${chatResponse.status} ${chatResponse.statusText}`);
      }

      const chatData = await chatResponse.json();
      console.log('Chat session created:', chatData);
      
      if (!chatData.success || !chatData.room_id) {
        throw new Error(chatData.error || 'Failed to get room ID');
      }

      // Step 2: Get access token
      const tokenResponse = await fetch('https://codeyoung-bk.vaaniresearch.com/api/get-chat-token/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          room_id: chatData.room_id,
          user_name: customerName || user_name
        })
      });

      if (!tokenResponse.ok) {
        const errorText = await tokenResponse.text();
        console.error('Token request failed:', errorText);
        throw new Error(`Failed to get access token: ${tokenResponse.status} ${tokenResponse.statusText}`);
      }

      const tokenData = await tokenResponse.json();
      console.log('Token received:', tokenData.success ? 'Success' : 'Failed');
      
      if (!tokenData.success || !tokenData.token) {
        throw new Error('Failed to get valid token');
      }

      // Step 3: Connect to LiveKit room
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      });
      setRoom(newRoom);

      // Set up event handlers
      newRoom.on(RoomEvent.Connected, () => {
        console.log('Connected to room successfully');
        setIsConnected(true);
        setIsConnecting(false);
        addMessage('system', 'Connected to chat. You can start messaging!', 'System');
        showToast('success', 'Connected', 'Chat session started successfully');
        
        // Focus input after connection
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      });

      newRoom.on(RoomEvent.Disconnected, (reason) => {
        console.log('Disconnected from room:', reason);
        setIsConnected(false);
        setIsConnecting(false);
        addMessage('system', 'Disconnected from chat', 'System');
        showToast('info', 'Disconnected', 'Chat session ended');
      });

      // SIMPLE ACCUMULATION APPROACH
      newRoom.on(RoomEvent.DataReceived, (payload: Uint8Array) => {
  try {
    const decoder = new TextDecoder();
    const message = JSON.parse(decoder.decode(payload));
    
    console.log('📨 Received message:', message);
    
    if (message.sender === 'agent') {
      setIsAgentTyping(false);
      
      // Handle ANY text message type - just display it
      if ((message.type === 'text' || message.type === 'text_chunk') && message.content && message.content.trim() !== '') {
        console.log('✅ Adding message to UI:', message.content);
        addMessage('agent', message.content, 'Agent');
      }
      // Ignore text_complete completely
      else if (message.type === 'text_complete') {
        console.log('🔄 Ignoring text_complete');
        // Do nothing
      }
      // Handle tool messages
      else if (message.type === 'tool_start') {
        setIsAgentTyping(true);
        addMessage('system', `🔧 ${message.content}`, 'System');
      } else if (message.type === 'tool_success') {
        addMessage('system', `✅ ${message.content}`, 'System');
      } else if (message.type === 'tool_error') {
        addMessage('system', `❌ ${message.content}`, 'System');
      }
    }
  } catch (error) {
    console.error('❌ Error parsing data:', error);
  }
});

      // Handle connection errors
      newRoom.on(RoomEvent.Reconnecting, () => {
        console.log('Reconnecting...');
        setIsConnecting(true);
        addMessage('system', 'Reconnecting...', 'System');
      });

      newRoom.on(RoomEvent.Reconnected, () => {
        console.log('Reconnected successfully');
        setIsConnecting(false);
        setIsConnected(true);
        addMessage('system', 'Reconnected successfully', 'System');
      });

      // Connect to the room with your LiveKit server URL
      const wsUrl = 'wss://setupforretell-hk7yl5xf.livekit.cloud';
      console.log('Connecting to LiveKit server:', wsUrl);
      await newRoom.connect(wsUrl, tokenData.token);

    } catch (error) {
      console.error('Connection error:', error);
      setIsConnecting(false);
      setConnectionError(error instanceof Error ? error.message : 'Failed to connect to chat');
      showToast('error', 'Connection Failed', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || !room || !isConnected) return;

    const messageToSend = currentMessage.trim();
    setCurrentMessage('');
    
    // Add user message to UI immediately
    addMessage('user', messageToSend, 'You');
    
    // Show agent typing indicator
    setIsAgentTyping(true);

    try {
      // Send message to agent via data channel
      const messageData = {
        type: 'user_message',
        content: messageToSend,
        timestamp: new Date().toISOString(),
        sender: 'user'
      };

      const encoder = new TextEncoder();
      const data = encoder.encode(JSON.stringify(messageData));
      
      await room.localParticipant.publishData(data, {
        reliable: true,
        topic: 'chat_message'
      });
      
      console.log('📤 Message sent:', messageData);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setIsAgentTyping(false);
      showToast('error', 'Send Failed', 'Failed to send message');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const disconnect = () => {
    if (room) {
      room.disconnect();
      setRoom(null);
    }
    setIsConnected(false);
    setIsConnecting(false);
    setMessages([]);
    setConnectionError(null);
    accumulatorRef.current = '';
    
    if (onClose) {
      onClose();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  return (
    <div className="chat-interface" style={{ 
      height: '600px', 
      width: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      border: '1px solid #ddd',
      borderRadius: '10px',
      overflow: 'hidden'
    }}>
      <Toast ref={toast} position="top-right" />
      
      {/* Header */}
      <div style={{ 
        background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
        color: 'white', 
        padding: '1rem', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.4rem' }}>Chat with AI Assistant</h3>
          <p style={{ margin: 0, fontSize: '0.9rem', opacity: 0.9 }}>
            {isConnecting ? 'Connecting...' : 
             isConnected ? '🟢 Connected' : 
             '🔴 Disconnected'}
          </p>
        </div>
        {isConnected && (
          <Button 
            icon="pi pi-times" 
            onClick={disconnect}
            className="p-button-text p-button-plain"
            style={{ color: 'white' }}
            tooltip="Disconnect"
          />
        )}
      </div>

      {/* Debug Info */}
      <div style={{ 
        background: '#f0f0f0', 
        padding: '0.5rem', 
        fontSize: '0.8rem',
        borderBottom: '1px solid #ddd'
      }}>
        Messages: {messages.length} | Accumulator: {accumulatorRef.current.length} chars
      </div>

      {/* Connection Error */}
      {connectionError && (
        <div style={{ 
          background: '#ffebee', 
          color: '#d32f2f', 
          padding: '1rem', 
          borderBottom: '1px solid #ffcdd2' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="pi pi-exclamation-triangle" />
            <span>{connectionError}</span>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div style={{ 
        flex: 1, 
        padding: '1rem', 
        overflowY: 'auto', 
        background: '#f8f9fa' 
      }}>
        {!isConnected && !isConnecting && !connectionError && (
          <div style={{ 
            textAlign: 'center', 
            padding: '2rem',
            color: '#6c757d' 
          }}>
            <i className="pi pi-comments" style={{ fontSize: '3rem', marginBottom: '1rem' }} />
            <h4>Welcome to Chat</h4>
            <p>Click "Connect to Chat" to start a conversation with our AI assistant.</p>
            <Button 
              label="Connect to Chat" 
              icon="pi pi-play"
              onClick={connectToChat}
              className="p-button-rounded p-button-lg"
              style={{ marginTop: '1rem' }}
            />
          </div>
        )}

        {isConnecting && (
          <div style={{ 
            textAlign: 'center', 
            padding: '2rem',
            color: '#6c757d' 
          }}>
            <ProgressSpinner style={{ width: '50px', height: '50px' }} />
            <p style={{ marginTop: '1rem' }}>Connecting to chat...</p>
          </div>
        )}

        {isConnected && messages.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: '2rem',
            color: '#6c757d' 
          }}>
            <p>Connected! Start typing a message below.</p>
          </div>
        )}

        {/* Messages */}
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '1rem'
            }}
          >
            <div
              style={{
                maxWidth: '70%',
                padding: '0.75rem 1rem',
                borderRadius: '15px',
                background: 
                  message.type === 'user' ? '#667eea' :
                  message.type === 'system' ? '#6c757d' : '#ffffff',
                color: message.type === 'agent' ? '#333' : '#ffffff',
                boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                border: message.type === 'agent' ? '1px solid #e9ecef' : 'none'
              }}
            >
              <div style={{ fontSize: '0.95rem', lineHeight: 1.4 }}>
                {message.content}
              </div>
              <div style={{ 
                fontSize: '0.75rem', 
                opacity: 0.7, 
                marginTop: '0.25rem',
                textAlign: 'right'
              }}>
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isAgentTyping && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '1rem' }}>
            <div style={{
              padding: '0.75rem 1rem',
              borderRadius: '15px',
              background: '#ffffff',
              border: '1px solid #e9ecef',
              boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ProgressSpinner style={{ width: '16px', height: '16px' }} />
                <span style={{ fontSize: '0.9rem', color: '#6c757d' }}>
                  Agent is responding...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      {isConnected && (
        <div style={{ 
          padding: '1rem', 
          borderTop: '1px solid #dee2e6',
          background: 'white'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <InputText
              ref={inputRef}
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              style={{ flex: 1 }}
              disabled={!isConnected || isAgentTyping}
            />
            <Button
              icon="pi pi-send"
              onClick={sendMessage}
              disabled={!currentMessage.trim() || !isConnected || isAgentTyping}
              className="p-button-rounded"
            />
          </div>
        </div>
      )}

      {connectionError && !isConnected && (
        <div style={{ 
          padding: '1rem', 
          borderTop: '1px solid #dee2e6',
          background: '#f8f9fa',
          textAlign: 'center'
        }}>
          <Button 
            label="Retry Connection" 
            icon="pi pi-refresh"
            onClick={connectToChat}
            className="p-button-rounded"
            disabled={isConnecting}
            loading={isConnecting}
          />
        </div>
      )}
    </div>
  );
};

export default ChatInterface;