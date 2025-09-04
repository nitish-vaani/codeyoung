// import React, { useState, useEffect, useRef } from 'react';
// import { Room, RoomEvent } from 'livekit-client';
// import { Button } from 'primereact/button';
// import { InputText } from 'primereact/inputtext';
// import { Toast } from 'primereact/toast';
// import { ProgressSpinner } from 'primereact/progressspinner';
// import { startFloatingChat, endFloatingChat } from '../../common/api';
// import './index.css';
// // import ChatDebugger from './ChatDebugger';

// interface ChatMessage {
//   id: string;
//   type: 'user' | 'agent' | 'system' | 'tool_start' | 'tool_success' | 'tool_error';
//   content: string;
//   timestamp: Date;
//   sender: string;
// }

// interface ChatSession {
//   sessionId: string;
//   roomId: string;
//   participantId: string;
//   token: string;
//   isActive: boolean;
// }

// const FloatingChatWidget: React.FC = () => {
//   // State management
//   const [isOpen, setIsOpen] = useState(false);
//   const [isConnected, setIsConnected] = useState(false);
//   const [isConnecting, setIsConnecting] = useState(false);
//   const [messages, setMessages] = useState<ChatMessage[]>([]);
//   const [currentMessage, setCurrentMessage] = useState('');
//   const [session, setSession] = useState<ChatSession | null>(null);
//   const [room, setRoom] = useState<Room | null>(null);
//   const [isAgentTyping, setIsAgentTyping] = useState(false);
//   const [connectionError, setConnectionError] = useState<string | null>(null);
//   const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  
//   // Refs
//   const toast = useRef<Toast>(null);
//   const messagesEndRef = useRef<HTMLDivElement>(null);
//   const inputRef = useRef<HTMLInputElement>(null);

//   // Auto-scroll to bottom when new messages arrive
//   useEffect(() => {
//     if (isOpen) {
//       messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//     }
//   }, [messages, isOpen]);

//   // Mark messages as read when widget is opened
//   useEffect(() => {
//     if (isOpen) {
//       setHasUnreadMessages(false);
//     }
//   }, [isOpen]);

//   // Focus input when chat opens
//   useEffect(() => {
//     if (isOpen && isConnected) {
//       setTimeout(() => {
//         inputRef.current?.focus();
//       }, 100);
//     }
//   }, [isOpen, isConnected]);

//   const showToast = (severity: 'success' | 'info' | 'warn' | 'error', summary: string, detail?: string) => {
//     toast.current?.show({ severity, summary, detail, life: 3000 });
//   };

//   const addMessage = (type: 'user' | 'agent' | 'system' | 'tool_start' | 'tool_success' | 'tool_error', content: string, sender: string = '') => {
//     const newMessage: ChatMessage = {
//       id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
//       type,
//       content,
//       timestamp: new Date(),
//       sender: sender || type
//     };
    
//     setMessages(prev => [...prev, newMessage]);
    
//     // Show unread indicator if widget is closed and it's an agent message
//     if (!isOpen && type === 'agent') {
//       setHasUnreadMessages(true);
//     }
//   };

//   // eslint-disable-next-line @typescript-eslint/no-unused-vars
// //   const generateUniqueParticipantId = (): string => {
// //     const userId = localStorage.getItem("fullName") || "user";
// //     const uuid = Math.random().toString(36).substring(2, 15);
// //     const date = new Date().toISOString().split('T')[0].replace(/-/g, '');
// //     return `${userId}_${uuid}_${date}`;
// //   };

//   const startChatSession = async () => {
//     try {
//       setIsConnecting(true);
//       setConnectionError(null);
      
//       const userId = localStorage.getItem("fullName");
//       const userName = localStorage.getItem("Name") || "Chat User";
      
//       if (!userId) {
//         throw new Error("Please login first");
//       }

//       console.log('🚀 Starting floating chat session...');

//       // Create chat session
//       const chatResponse = await startFloatingChat({
//         user_id: userId,
//         customer_name: userName,
//         agent_id: "chat_agent_1"
//       });

//       if (!chatResponse.data.success) {
//         throw new Error(chatResponse.data.message || 'Failed to create chat session');
//       }

//       const { session_id, room_id, participant_id, token } = chatResponse.data;
      
//       console.log('✅ Chat session created:', { session_id, room_id, participant_id });

//       // Store session info
//       const newSession: ChatSession = {
//         sessionId: session_id,
//         roomId: room_id,
//         participantId: participant_id,
//         token: token,
//         isActive: true
//       };
//       setSession(newSession);

//       // Connect to LiveKit room
//       const newRoom = new Room({
//         adaptiveStream: true,
//         dynacast: true,
//       });
//       setRoom(newRoom);

//       // Set up event handlers
//       newRoom.on(RoomEvent.Connected, () => {
//         console.log('🔗 Connected to chat room');
//         setIsConnected(true);
//         setIsConnecting(false);
//         addMessage('system', 'Connected! How can I help you today?', 'System');
//         showToast('success', 'Chat Started', 'You can now start messaging');
//       });

//       newRoom.on(RoomEvent.Disconnected, (reason) => {
//         console.log('❌ Disconnected from chat room:', reason);
//         setIsConnected(false);
//         setIsConnecting(false);
//         addMessage('system', 'Chat session ended', 'System');
//       });

//       // Handle incoming messages from agent
//       newRoom.on(RoomEvent.DataReceived, (payload: Uint8Array) => {
//         try {
//           const decoder = new TextDecoder();
//           const message = JSON.parse(decoder.decode(payload));
          
//           console.log('📨 Received message:', message);
          
//           if (message.sender === 'agent') {
//             setIsAgentTyping(false);
            
//             if ((message.type === 'text' || message.type === 'text_chunk') && message.content && message.content.trim() !== '') {
//               addMessage('agent', message.content, 'Agent');
//             } else if (message.type === 'tool_start') {
//               setIsAgentTyping(true);
//               addMessage('system', `🔧 ${message.content}`, 'System');
//             } else if (message.type === 'tool_success') {
//               addMessage('system', `✅ ${message.content}`, 'System');
//             } else if (message.type === 'tool_error') {
//               addMessage('system', `❌ ${message.content}`, 'System');
//             }
//           }
//         } catch (error) {
//           console.error('❌ Error parsing message:', error);
//         }
//       });

//       // Connect to the room
//       const wsUrl = 'wss://setupforretell-hk7yl5xf.livekit.cloud';
//       await newRoom.connect(wsUrl, token);

//     } catch (error) {
//       console.error('❌ Error starting chat:', error);
//       setIsConnecting(false);
//       setConnectionError(error instanceof Error ? error.message : 'Failed to start chat');
//       showToast('error', 'Connection Failed', error instanceof Error ? error.message : 'Unknown error');
//     }
//   };

//   const endChatSession = async () => {
//     try {
//       if (session) {
//         await endFloatingChat(session.sessionId);
//       }
      
//       if (room) {
//         room.disconnect();
//         setRoom(null);
//       }
      
//       setSession(null);
//       setIsConnected(false);
//       setMessages([]);
//       setConnectionError(null);
//       setIsAgentTyping(false);
      
//       showToast('info', 'Chat Ended', 'Chat session has been ended');
//     } catch (error) {
//       console.error('❌ Error ending chat:', error);
//       showToast('error', 'Error', 'Failed to end chat session properly');
//     }
//   };

//   const sendMessage = async () => {
//     if (!currentMessage.trim() || !room || !isConnected) return;

//     const messageToSend = currentMessage.trim();
//     setCurrentMessage('');
    
//     // Add user message to UI immediately
//     addMessage('user', messageToSend, 'You');
    
//     // Show agent typing indicator
//     setIsAgentTyping(true);

//     try {
//       // Send message to agent via data channel
//       const messageData = {
//         type: 'user_message',
//         content: messageToSend,
//         timestamp: new Date().toISOString(),
//         sender: 'user'
//       };

//       const encoder = new TextEncoder();
//       const data = encoder.encode(JSON.stringify(messageData));
      
//       await room.localParticipant.publishData(data, {
//         reliable: true,
//         topic: 'chat_message'
//       });
      
//       console.log('📤 Message sent:', messageData);
      
//     } catch (error) {
//       console.error('❌ Error sending message:', error);
//       setIsAgentTyping(false);
//       showToast('error', 'Send Failed', 'Failed to send message');
//     }
//   };

//   const handleKeyPress = (e: React.KeyboardEvent) => {
//     if (e.key === 'Enter' && !e.shiftKey) {
//       e.preventDefault();
//       sendMessage();
//     }
//   };

//   const toggleWidget = () => {
//     if (!isOpen && !isConnected && !session) {
//       // Opening for the first time, start a new session
//       setIsOpen(true);
//       startChatSession();
//     } else {
//       // Just toggle visibility
//       setIsOpen(!isOpen);
//     }
//   };

//   const formatTime = (date: Date) => {
//     return date.toLocaleTimeString('en-US', { 
//       hour: '2-digit', 
//       minute: '2-digit',
//       hour12: true 
//     });
//   };

//   return (
//     <>
//       <Toast ref={toast} position="top-right" />
      
//       {/* Floating Chat Button */}
//       <div className={`floating-chat-button ${hasUnreadMessages ? 'has-unread' : ''}`}>
//         <Button
//           icon={isOpen ? "pi pi-times" : "pi pi-comments"}
//           className="p-button-rounded p-button-help"
//           onClick={toggleWidget}
//           tooltip={isOpen ? "Close Chat" : "Start Chat"}
//           tooltipOptions={{ position: 'left' }}
//         />
//         {hasUnreadMessages && (
//           <div className="unread-indicator">
//             <span className="unread-dot"></span>
//           </div>
//         )}
//       </div>

//       {/* Chat Widget */}
//       {isOpen && (
//         <div className="floating-chat-widget">
//           {/* Header */}
//           <div className="chat-header">
//             <div className="header-info">
//               <h4>💬 Chat Support</h4>
//               <p className="status">
//                 {isConnecting ? 'Connecting...' : 
//                  isConnected ? '🟢 Online' : 
//                  '🔴 Offline'}
//               </p>
//             </div>
//             <div className="header-actions">
//               {isConnected && (
//                 <Button 
//                   icon="pi pi-trash" 
//                   className="p-button-text p-button-plain p-button-sm"
//                   onClick={endChatSession}
//                   tooltip="End Chat"
//                 />
//               )}
//               <Button 
//                 icon="pi pi-minus" 
//                 className="p-button-text p-button-plain p-button-sm"
//                 onClick={() => setIsOpen(false)}
//                 tooltip="Minimize"
//               />
//             </div>
//           </div>

//           {/* Messages Area */}
//           <div className="chat-messages">
//             {!isConnected && !isConnecting && !connectionError && (
//               <div className="welcome-screen">
//                 <div className="welcome-icon">💬</div>
//                 <h4>Welcome to Chat Support</h4>
//                 <p>Click the button below to start chatting with our AI assistant.</p>
//                 <Button 
//                   label="Start Chat" 
//                   icon="pi pi-play"
//                   onClick={startChatSession}
//                   className="p-button-rounded"
//                 />
//               </div>
//             )}

//             {isConnecting && (
//               <div className="connecting-screen">
//                 <ProgressSpinner style={{ width: '50px', height: '50px' }} />
//                 <p>Connecting to chat...</p>
//               </div>
//             )}

//             {connectionError && (
//               <div className="error-screen">
//                 <div className="error-icon">⚠️</div>
//                 <h4>Connection Failed</h4>
//                 <p>{connectionError}</p>
//                 <Button 
//                   label="Try Again" 
//                   icon="pi pi-refresh"
//                   onClick={startChatSession}
//                   className="p-button-rounded p-button-sm"
//                 />
//               </div>
//             )}

//             {/* Messages */}
//             {messages.map((message) => (
//               <div
//                 key={message.id}
//                 className={`message ${message.type === 'user' ? 'message-user' : 
//                              message.type === 'system' ? 'message-system' : 'message-agent'}`}
//               >
//                 <div className="message-content">
//                   <div className="message-text">{message.content}</div>
//                   <div className="message-time">{formatTime(message.timestamp)}</div>
//                 </div>
//               </div>
//             ))}

//             {/* Typing Indicator */}
//             {isAgentTyping && (
//               <div className="message message-agent">
//                 <div className="message-content">
//                   <div className="typing-indicator">
//                     <div className="typing-dots">
//                       <span></span>
//                       <span></span>
//                       <span></span>
//                     </div>
//                     <span className="typing-text">Agent is typing...</span>
//                   </div>
//                 </div>
//               </div>
//             )}

//             <div ref={messagesEndRef} />
//           </div>

//           {/* Input Area */}
//           {isConnected && (
//             <div className="chat-input">
//               <div className="input-container">
//                 <InputText
//                   ref={inputRef}
//                   value={currentMessage}
//                   onChange={(e) => setCurrentMessage(e.target.value)}
//                   onKeyPress={handleKeyPress}
//                   placeholder="Type your message..."
//                   disabled={!isConnected || isAgentTyping}
//                   className="message-input"
//                 />
//                 <Button
//                   icon="pi pi-send"
//                   onClick={sendMessage}
//                   disabled={!currentMessage.trim() || !isConnected || isAgentTyping}
//                   className="send-button"
//                 />
//               </div>
//             </div>
//           )}
//         </div>
//       )}
//     </>
//   );
// };

// export default FloatingChatWidget;



import React, { useState, useEffect, useRef } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { triggerChat, getChatToken } from '../../common/api';
import './index.css';

interface ChatMessage {
  id: string;
  type: 'user' | 'agent' | 'system' | 'tool_start' | 'tool_success' | 'tool_error';
  content: string;
  timestamp: Date;
  sender: string;
}

interface ChatSession {
  sessionId: string;
  roomId: string;
  participantId: string;
  isActive: boolean;
}

const FloatingChatWidget: React.FC = () => {
  // State management
  const [isOpen, setIsOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [session, setSession] = useState<ChatSession | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  
  // Refs
  const toast = useRef<Toast>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Mark messages as read when widget is opened
  useEffect(() => {
    if (isOpen) {
      setHasUnreadMessages(false);
    }
  }, [isOpen]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && isConnected) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [isOpen, isConnected]);

  const showToast = (severity: 'success' | 'info' | 'warn' | 'error', summary: string, detail?: string) => {
    toast.current?.show({ severity, summary, detail, life: 3000 });
  };

  const addMessage = (type: 'user' | 'agent' | 'system' | 'tool_start' | 'tool_success' | 'tool_error', content: string, sender: string = '') => {
    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      content,
      timestamp: new Date(),
      sender: sender || type
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Show unread indicator if widget is closed and it's an agent message
    if (!isOpen && type === 'agent') {
      setHasUnreadMessages(true);
    }
  };

  const generateCustomParticipantId = (): string => {
    const userId = localStorage.getItem("fullName") || "user";
    const uuid = Math.random().toString(36).substring(2, 10); // 8 character UUID
    const date = new Date().toISOString().split('T')[0].replace(/-/g, ''); // YYYYMMDD format
    return `${userId}_${uuid}_${date}`;
  };

  const startChatSession = async () => {
    try {
      setIsConnecting(true);
      setConnectionError(null);
      
      const userId = localStorage.getItem("fullName");
      const userName = localStorage.getItem("Name") || "Chat User";
      
      if (!userId) {
        throw new Error("Please login first");
      }

      console.log('🚀 Starting floating chat session...');

      // Generate custom participant ID in the format: userId_uuid_date
      const customParticipantId = generateCustomParticipantId();
      console.log('Generated participant ID:', customParticipantId);

      // Step 1: Create chat session using existing triggerChat API
      const chatResponse = await triggerChat({
        user_id: userId,
        agent_id: "3", // Using same agent as your chat page
        name: userName,
        agent_name: "Codeyoung Agent",
        session_id: customParticipantId // Use our custom participant ID as session ID
      });

      if (!chatResponse.data.success) {
        throw new Error(chatResponse.data.message || 'Failed to create chat session');
      }

      const { room_id } = chatResponse.data;
      console.log('✅ Chat session created with room_id:', room_id);

      // Step 2: Get access token using existing getChatToken API
      const tokenResponse = await getChatToken({
        room_id: room_id,
        user_name: userName
      });

      if (!tokenResponse.data.success) {
        throw new Error('Failed to get access token');
      }

      const { token } = tokenResponse.data;
      console.log('✅ Access token received');

      // Store session info
      const newSession: ChatSession = {
        sessionId: room_id,
        roomId: room_id,
        participantId: customParticipantId,
        isActive: true
      };
      setSession(newSession);

      // Step 3: Connect to LiveKit room (same as chat page)
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      });
      setRoom(newRoom);

      // Set up event handlers
      newRoom.on(RoomEvent.Connected, () => {
        console.log('🔗 Connected to floating chat room');
        setIsConnected(true);
        setIsConnecting(false);
        addMessage('system', 'Connected! How can I help you today?', 'System');
        showToast('success', 'Chat Started', 'You can now start messaging');
      });

      newRoom.on(RoomEvent.Disconnected, (reason) => {
        console.log('❌ Disconnected from chat room:', reason);
        setIsConnected(false);
        setIsConnecting(false);
        addMessage('system', 'Chat session ended', 'System');
      });

      // Handle incoming messages from agent (same logic as chat page)
      newRoom.on(RoomEvent.DataReceived, (payload: Uint8Array) => {
        try {
          const decoder = new TextDecoder();
          const message = JSON.parse(decoder.decode(payload));
          
          console.log('📨 Received message:', message);
          
          if (message.sender === 'agent') {
            setIsAgentTyping(false);
            
            if ((message.type === 'text' || message.type === 'text_chunk') && message.content && message.content.trim() !== '') {
              console.log('✅ Adding message to UI:', message.content);
              addMessage('agent', message.content, 'Agent');
            } else if (message.type === 'text_complete') {
              console.log('🔄 Ignoring text_complete');
              // Do nothing
            } else if (message.type === 'tool_start') {
              setIsAgentTyping(true);
              addMessage('system', `🔧 ${message.content}`, 'System');
            } else if (message.type === 'tool_success') {
              addMessage('system', `✅ ${message.content}`, 'System');
            } else if (message.type === 'tool_error') {
              addMessage('system', `❌ ${message.content}`, 'System');
            }
          }
        } catch (error) {
          console.error('❌ Error parsing message:', error);
        }
      });

      // Reconnection handlers
      newRoom.on(RoomEvent.Reconnecting, () => {
        console.log('🔄 Reconnecting...');
        setIsConnecting(true);
        addMessage('system', 'Reconnecting...', 'System');
      });

      newRoom.on(RoomEvent.Reconnected, () => {
        console.log('✅ Reconnected successfully');
        setIsConnecting(false);
        setIsConnected(true);
        addMessage('system', 'Reconnected successfully', 'System');
      });

      // Connect to the room with LiveKit server URL
      const wsUrl = 'wss://setupforretell-hk7yl5xf.livekit.cloud';
      console.log('🔗 Connecting to LiveKit server:', wsUrl);
      await newRoom.connect(wsUrl, token);

    } catch (error) {
      console.error('❌ Error starting floating chat:', error);
      setIsConnecting(false);
      setConnectionError(error instanceof Error ? error.message : 'Failed to start chat');
      showToast('error', 'Connection Failed', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const endChatSession = async () => {
    try {
      if (room) {
        room.disconnect();
        setRoom(null);
      }
      
      setSession(null);
      setIsConnected(false);
      setMessages([]);
      setConnectionError(null);
      setIsAgentTyping(false);
      
      showToast('info', 'Chat Ended', 'Chat session has been ended');
    } catch (error) {
      console.error('❌ Error ending chat:', error);
      showToast('error', 'Error', 'Failed to end chat session properly');
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
      // Send message to agent via data channel (same as chat page)
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
      console.error('❌ Error sending message:', error);
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

  const toggleWidget = () => {
    if (!isOpen && !isConnected && !session) {
      // Opening for the first time, start a new session
      setIsOpen(true);
      startChatSession();
    } else {
      // Just toggle visibility
      setIsOpen(!isOpen);
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
    <>
      <Toast ref={toast} position="top-right" />
      
      {/* Floating Chat Button */}
      <div className={`floating-chat-button ${hasUnreadMessages ? 'has-unread' : ''}`}>
        <Button
          icon={isOpen ? "pi pi-times" : "pi pi-comments"}
          className="p-button-rounded p-button-help"
          onClick={toggleWidget}
          tooltip={isOpen ? "Close Chat" : "Start Chat"}
          tooltipOptions={{ position: 'left' }}
        />
        {hasUnreadMessages && (
          <div className="unread-indicator">
            <span className="unread-dot"></span>
          </div>
        )}
      </div>

      {/* Chat Widget */}
      {isOpen && (
        <div className="floating-chat-widget">
          {/* Header */}
          <div className="chat-header">
            <div className="header-info">
              <h4>💬 Chat Support</h4>
              <p className="status">
                {isConnecting ? 'Connecting...' : 
                 isConnected ? '🟢 Online' : 
                 '🔴 Offline'}
              </p>
            </div>
            <div className="header-actions">
              {isConnected && (
                <Button 
                  icon="pi pi-trash" 
                  className="p-button-text p-button-plain p-button-sm"
                  onClick={endChatSession}
                  tooltip="End Chat"
                />
              )}
              <Button 
                icon="pi pi-minus" 
                className="p-button-text p-button-plain p-button-sm"
                onClick={() => setIsOpen(false)}
                tooltip="Minimize"
              />
            </div>
          </div>

          {/* Messages Area */}
          <div className="chat-messages">
            {!isConnected && !isConnecting && !connectionError && (
              <div className="welcome-screen">
                <div className="welcome-icon">💬</div>
                <h4>Welcome to Chat Support</h4>
                <p>Click the button below to start chatting with our AI assistant.</p>
                <Button 
                  label="Start Chat" 
                  icon="pi pi-play"
                  onClick={startChatSession}
                  className="p-button-rounded"
                />
              </div>
            )}

            {isConnecting && (
              <div className="connecting-screen">
                <ProgressSpinner style={{ width: '50px', height: '50px' }} />
                <p>Connecting to chat...</p>
              </div>
            )}

            {connectionError && (
              <div className="error-screen">
                <div className="error-icon">⚠️</div>
                <h4>Connection Failed</h4>
                <p>{connectionError}</p>
                <Button 
                  label="Try Again" 
                  icon="pi pi-refresh"
                  onClick={startChatSession}
                  className="p-button-rounded p-button-sm"
                />
              </div>
            )}

            {/* Messages */}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.type === 'user' ? 'message-user' : 
                             message.type === 'system' ? 'message-system' : 'message-agent'}`}
              >
                <div className="message-content">
                  <div className="message-text">{message.content}</div>
                  <div className="message-time">{formatTime(message.timestamp)}</div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isAgentTyping && (
              <div className="message message-agent">
                <div className="message-content">
                  <div className="typing-indicator">
                    <div className="typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span className="typing-text">Agent is typing...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          {isConnected && (
            <div className="chat-input">
              <div className="input-container">
                <InputText
                  ref={inputRef}
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={!isConnected || isAgentTyping}
                  className="message-input"
                />
                <Button
                  icon="pi pi-send"
                  onClick={sendMessage}
                  disabled={!currentMessage.trim() || !isConnected || isAgentTyping}
                  className="send-button"
                />
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default FloatingChatWidget;