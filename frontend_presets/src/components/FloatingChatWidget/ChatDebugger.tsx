import React, { useState } from 'react';
import { Button } from 'primereact/button';

interface ChatDebuggerProps {
  messages: any[];
  session: any;
  room: any;
  isConnected: boolean;
}

const ChatDebugger: React.FC<ChatDebuggerProps> = ({ messages, session, room, isConnected }) => {
  const [showDebug, setShowDebug] = useState(false);

  if (process.env.NODE_ENV === 'production') {
    return null; // Don't show in production
  }

  return (
    <>
      <Button 
        icon="pi pi-bug" 
        className="p-button-text p-button-plain p-button-sm"
        onClick={() => setShowDebug(!showDebug)}
        style={{
          position: 'fixed',
          bottom: '130px',
          right: '20px',
          zIndex: 1002
        }}
      />
      
      {showDebug && (
        <div style={{
          position: 'fixed',
          bottom: '170px',
          right: '20px',
          width: '300px',
          maxHeight: '200px',
          background: 'black',
          color: 'lime',
          padding: '10px',
          borderRadius: '5px',
          fontSize: '12px',
          fontFamily: 'monospace',
          overflow: 'auto',
          zIndex: 1001
        }}>
          <div>🔗 Connected: {isConnected ? 'YES' : 'NO'}</div>
          <div>📨 Messages: {messages.length}</div>
          <div>🏠 Room: {room ? 'Connected' : 'None'}</div>
          <div>📋 Session: {session ? session.sessionId : 'None'}</div>
          <div>👤 Participant: {session ? session.participantId : 'None'}</div>
          <hr style={{margin: '5px 0'}} />
          <div>Recent messages:</div>
          {messages.slice(-3).map((msg, i) => (
            <div key={i}>
              {msg.sender}: {msg.content.substring(0, 30)}...
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default ChatDebugger;