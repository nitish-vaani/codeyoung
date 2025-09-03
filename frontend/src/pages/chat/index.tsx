import React, { useState, useEffect, useRef } from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { IconField } from 'primereact/iconfield';
import { InputIcon } from 'primereact/inputicon';
import { Toast } from 'primereact/toast';
import ChatInterface from '../../components/ChatInterface';
import { getAllModels } from '../../common/api';

type Model = {
    model_id: string,
    model_name: string,
}

const ChatPage: React.FC = () => {
  const [showChat, setShowChat] = useState(false);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [loading] = useState(false);
  const toast = useRef<Toast>(null);

  const showToast = (severity: 'success' | 'info' | 'warn' | 'error', summary: string, detail?: string) => {
    toast.current?.show({ severity, summary, detail, life: 3000 });
  };

  useEffect(() => {
    // Load available models/agents
    getAllModels()
      .then((data: any) => {
        setModels(data.data);
      })
      .catch((error) => {
        console.error("Error fetching models:", error);
        showToast('error', 'Error', 'Failed to load available agents');
      });
  }, []);

  const startChat = () => {
    if (!selectedModel || !customerName.trim()) {
      showToast('warn', 'Missing Information', 'Please select an agent and enter your name');
      return;
    }

    setShowChat(true);
  };

  const endChat = () => {
    setShowChat(false);
    setCustomerName('');
    setSelectedModel(null);
  };

  if (showChat) {
    return (
      <div style={{
        background: '#f5f1ff',
        minHeight: '85vh',
        padding: '2rem',
        borderRadius: '20px',
        margin: '1vh 3vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <div style={{ 
          textAlign: 'center', 
          marginBottom: '2rem',
          maxWidth: '800px'
        }}>
          <h1 style={{ 
            fontSize: '2.5rem', 
            fontWeight: 300, 
            color: '#333',
            marginBottom: '0.5rem'
          }}>
            Chatting with {selectedModel?.model_name}
          </h1>
          <p style={{
            fontSize: '1.1rem',
            color: '#666',
            margin: '0'
          }}>
            Customer: {customerName}
          </p>
          <Button 
            label="End Chat" 
            icon="pi pi-times"
            onClick={endChat}
            className="p-button-outlined p-button-danger"
            style={{ marginTop: '1rem' }}
          />
        </div>

        <div style={{
          width: '100%',
          maxWidth: '900px',
          background: 'white',
          borderRadius: '15px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden'
        }}>
          <ChatInterface 
            selectedAgent={selectedModel || undefined}
            customerName={customerName}
            onClose={endChat}
          />
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: '#f5f1ff',
      minHeight: '85vh',
      padding: '2rem',
      borderRadius: '20px',
      margin: '1vh 3vw',
      display: 'flex',
      flexDirection: 'row',
      gap: '2rem',
      justifyContent: 'space-between'
    }}>
      <Toast ref={toast} position="bottom-right" />
      
      {/* Left side - Description */}
      <div style={{ flex: 1, paddingLeft: '1rem' }}>
        <h1 style={{ 
          fontSize: '3.1rem', 
          fontWeight: 300, 
          marginBottom: '2rem',
          color: '#333'
        }}>
          Try our <span style={{ fontWeight: 500 }}>AI Chat agents</span> today!
        </h1>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '3rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              width: '2rem',
              height: '2rem',
              backgroundColor: 'white',
              borderRadius: '50%',
              border: 'none'
            }}></div>
            <span style={{ fontSize: '1.5rem', fontWeight: 100 }}>
              Natural text conversations with intelligent responses
            </span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              width: '2rem',
              height: '2rem',
              backgroundColor: 'white',
              borderRadius: '50%',
              border: 'none'
            }}></div>
            <span style={{ fontSize: '1.5rem', fontWeight: 100 }}>
              Real-time messaging with instant AI responses
            </span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              width: '2rem',
              height: '2rem',
              backgroundColor: 'white',
              borderRadius: '50%',
              border: 'none'
            }}></div>
            <span style={{ fontSize: '1.5rem', fontWeight: 100 }}>
              Fully Secure, Compliant & Automated conversations
            </span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{
              width: '2rem',
              height: '2rem',
              backgroundColor: 'white',
              borderRadius: '50%',
              border: 'none'
            }}></div>
            <span style={{ fontSize: '1.5rem', fontWeight: 100 }}>
              Can be tailored and hyper-personalized for every user
            </span>
          </div>
        </div>

        <div style={{
          fontSize: '1.4rem',
          fontWeight: 400,
          color: '#393939',
          lineHeight: '2rem',
          maxWidth: '40vw'
        }}>
          We're working hard towards optimizing our AI and improving its performance.
          You can help us by providing your valuable{' '}
          <span style={{ 
            fontWeight: 800,
            display: 'inline-flex',
            alignItems: 'baseline',
            gap: '5px'
          }}>
            <i className="pi pi-comment" style={{ fontSize: '1.3rem', position: 'relative', top: '5px' }}></i>
            feedback
          </span>
          {' '}about your chat experience.
        </div>
      </div>

      {/* Right side - Chat Setup */}
      <Card style={{
        width: '30%',
        backgroundColor: 'white',
        borderRadius: '15px',
        height: 'fit-content'
      }}>
        <div style={{ padding: '1.5rem' }}>
          <h1 style={{ 
            fontSize: '2rem', 
            fontWeight: 400, 
            textAlign: 'center',
            marginBottom: '2rem',
            color: '#333'
          }}>
            Start Chat Session
          </h1>

          <div style={{ marginBottom: '2rem' }}>
            <IconField iconPosition="right">
              <InputIcon className="pi pi-user" />
              <InputText 
                placeholder="Your name" 
                value={customerName} 
                onChange={(e) => setCustomerName(e.target.value)}
                disabled={loading}
                style={{ width: '100%' }}
              />
            </IconField>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ 
              fontSize: '1.2rem', 
              fontWeight: 400, 
              marginBottom: '1rem',
              color: '#333'
            }}>
              SELECT AGENT:
            </h3>
            <Dropdown 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.value)} 
              options={models} 
              optionLabel="model_name"
              placeholder="Select an AI Agent" 
              style={{ width: '100%' }}
              disabled={loading}
            />
          </div>

          <Button 
            label="START CHAT SESSION" 
            icon="pi pi-comments" 
            onClick={startChat}
            disabled={!selectedModel || !customerName.trim() || loading}
            loading={loading}
            style={{
              width: '100%',
              fontSize: '1.1rem',
              borderRadius: '12px',
              marginBottom: '1.5rem',
              backgroundColor: 'rgb(54, 54, 54)',
              border: 'none',
              color: 'white',
              padding: '0.75rem'
            }}
          />

          <div style={{ 
            fontSize: '0.9rem', 
            color: '#666', 
            textAlign: 'center',
            lineHeight: '1.4'
          }}>
            Click the button above to start a real-time chat session with your selected AI agent.
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChatPage;