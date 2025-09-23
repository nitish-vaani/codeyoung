import { DataTable, DataTableSelectionMultipleChangeEvent } from 'primereact/datatable';
import './index.css'
import { Column } from 'primereact/column';
import { Sidebar } from 'primereact/sidebar';
import { useEffect, useRef, useState } from 'react';
import { getCallDetails, getCallHistory, getChatHistory, getAllSessions } from '../../common/api';
import { Toast } from 'primereact/toast';
import { useNavigate } from 'react-router-dom';
import { pagePaths } from '../../common/constants';
import { MoonLoader, ScaleLoader } from 'react-spinners';
import ConversationEval from '../../components/conversation-eval';
import EntityExtraction from '../../components/entity-extraction';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Calendar } from 'primereact/calendar';
import { Dropdown } from 'primereact/dropdown';
import { ConditionalWrapper, useConfig } from '../../components/ConditionalWrapper';

interface HistoryProps {
  // Add any props here if needed - currently none are required
}

interface HistoryRecord {
    id?: string;
    name?: string;
    customer_name?: string;
    End_time?: string;
    started_at?: string;
    ended_at?: string;
    duration_ms?: string;
    direction?: string;
    from_number?: string;
    to_number?: string;
    call_status?: string;
    status?: string;
    recording_api?: string;
    transcript?: string;
    summary?: string;
    message_count?: number;
    session_id?: string;
    agent_name?: string;
    type: 'call' | 'chat';
    [key: string]: any;
}

interface CallDetailsResponse {
    transcription: string;
    entity: any;
    conversation_eval: any;
    summary: string;
}

const History: React.FC<HistoryProps> = () => {
    const navigate = useNavigate();
    const toast = useRef<Toast>(null);
    const { isComponentEnabled } = useConfig();
    const isSelectionEnabled = isComponentEnabled('call_history.selection_checkboxes');

    const show = (summary: string, severity: 'error' | 'info' | 'success' = 'error') => {
        toast.current?.show({ severity, summary, life: 3000 });
    };

    const [visible, setVisible] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [list, setList] = useState<HistoryRecord[]>([]);
    const [filteredList, setFilteredList] = useState<HistoryRecord[]>([]);
    
    // View mode state
    const [viewMode, setViewMode] = useState<'calls' | 'chats' | 'all'>('calls');
    
    // Audio states - but with error handling
    const [audioLoading, setAudioLoading] = useState<boolean>(false);
    const [audioSrc, setAudioSrc] = useState<string|undefined>();
    const [audioError, setAudioError] = useState<string | null>(null);
    
    const [sideBarData, setSideBarData] = useState<any>();
    const [detailsLoading, setDetailsLoading] = useState<boolean>(false);
    const [conversationEval, setConversationEval] = useState<any>(null);
    const [entityData, setEntityData] = useState<any>(null);
    
    // Filter states
    const [selectedRecords, setSelectedRecords] = useState<HistoryRecord[]>([]);
    const [showFilters, setShowFilters] = useState<boolean>(false);
    const [searchText, setSearchText] = useState<string>('');
    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);
    const [selectedStatus, setSelectedStatus] = useState<string>('');
    const [selectedDirection, setSelectedDirection] = useState<string>('');

    // Filter options - updated for both calls and chats
    const statusOptions = [
        { label: 'All Status', value: '' },
        { label: 'Completed', value: 'completed' },
        { label: 'Active', value: 'active' },
        { label: 'Failed', value: 'failed' },
        { label: 'In Progress', value: 'in-progress' },
        { label: 'Busy', value: 'busy' },
        { label: 'No Answer', value: 'no-answer' }
    ];

    const directionOptions = [
        { label: 'All Types', value: '' },
        { label: 'Inbound', value: 'inbound' },
        { label: 'Outbound', value: 'outbound' },
        { label: 'Chat', value: 'chat' }
    ];

    // Modified audio fetching with graceful error handling
    useEffect(() => {
        const fetchAudioStream = async () => {
            if (!sideBarData?.recording_api) {
                if (sideBarData?.type === 'chat') {
                    setAudioError("No audio recording available for chat sessions");
                } else {
                    setAudioError("No recording URL available");
                }
                return;
            }

            try {
                setAudioLoading(true);
                setAudioError(null);
                
                const url: string = sideBarData.recording_api;   
                const response = await fetch(url);
                
                if (!response.ok) {
                    // Handle different error types
                    if (response.status === 404) {
                        setAudioError("Audio recording not found for this call");
                    } else if (response.status === 403) {
                        setAudioError("Access denied to audio recording");
                    } else {
                        setAudioError(`Audio not available (Error: ${response.status})`);
                    }
                    return;
                }

                const audioBlob = await response.blob();
                
                // Check if the blob is actually audio content
                if (audioBlob.size === 0) {
                    setAudioError("Audio recording is empty");
                    return;
                }
                
                const audioUrl = URL.createObjectURL(audioBlob);
                setAudioSrc(audioUrl);
                setAudioError(null);
                
            } catch (error) {
                console.error("Error streaming audio:", error);
                setAudioError("Unable to load audio recording");
            } finally {
                setAudioLoading(false);
            }
        };

        if (sideBarData?.recording_api && sideBarData?.type !== 'chat' && isComponentEnabled('call_history.call_details_sidebar.audio_recording')) {
            fetchAudioStream();
        } else if (sideBarData?.type === 'chat') {
            setAudioError("No audio recording available for chat sessions");
            setAudioSrc(undefined);
        } else {
            setAudioError("No recording available");
            setAudioSrc(undefined);
        }

        return () => {
            if (audioSrc) {
                URL.revokeObjectURL(audioSrc);
                setAudioSrc(undefined);
            }
        };
    }, [sideBarData, isComponentEnabled]);

    // Apply filters when filter criteria change
    useEffect(() => {
        let filtered = [...list];

        // Text search filter
        if (searchText) {
            filtered = filtered.filter(record => 
                record.name?.toLowerCase().includes(searchText.toLowerCase()) ||
                record.customer_name?.toLowerCase().includes(searchText.toLowerCase()) ||
                record.from_number?.includes(searchText) ||
                record.to_number?.includes(searchText) ||
                record.agent_name?.toLowerCase().includes(searchText.toLowerCase())
            );
        }

        // Date range filter
        if (startDate || endDate) {
            filtered = filtered.filter(record => {
                const recordDate = record.type === 'chat' ? 
                    new Date(record.started_at || '') : 
                    new Date(record.End_time || '');
                    
                if (startDate && recordDate < startDate) return false;
                if (endDate && recordDate > endDate) return false;
                return true;
            });
        }

        // Status filter
        if (selectedStatus) {
            filtered = filtered.filter(record => {
                const status = record.type === 'chat' ? record.status : record.call_status;
                return status?.toLowerCase() === selectedStatus.toLowerCase();
            });
        }

        // Direction filter
        if (selectedDirection) {
            if (selectedDirection === 'chat') {
                filtered = filtered.filter(record => record.type === 'chat');
            } else {
                filtered = filtered.filter(record => 
                    record.type === 'call' && 
                    record.direction?.toLowerCase() === selectedDirection.toLowerCase()
                );
            }
        }

        setFilteredList(filtered);
    }, [list, searchText, startDate, endDate, selectedStatus, selectedDirection]);

    function formatDuration(seconds: number) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    }

    function formatDurationMillis(milliseconds: number) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        return formatDuration(totalSeconds);
    }

    const dateTime = (input: number | string) => {
        const date = new Date(input);
        return date.toLocaleString();
    }

    // Load data based on view mode
    useEffect(() => {
        const user_id = localStorage.getItem("fullName")
        if (user_id == null) {
            show("please login first");
            navigate(pagePaths.signin);
        } else {
            setLoading(true);
            
            const loadData = async () => {
                try {
                    if (viewMode === 'calls') {
                        const data = await getCallHistory(user_id);
                        const res = data.data.map(({Name, ...d}: { Name: { name: any; }; duration_ms: number; End_time: number; }, index: number) => ({
                            ...d,
                            id: `call_${index}`,
                            name: Name.name,
                            duration_ms: formatDurationMillis(d.duration_ms),
                            End_time: dateTime(d.End_time),
                            type: 'call' as const
                        }));
                        setList(res);
                    } else if (viewMode === 'chats') {
                        const data = await getChatHistory(user_id);
                        const res = data.data.map((chat: any, index: number) => ({
                            ...chat,
                            id: `chat_${index}`,
                            name: chat.customer_name,
                            End_time: chat.ended_at ? dateTime(chat.ended_at) : 'Active',
                            duration_ms: chat.message_count ? `${chat.message_count} messages` : '0 messages',
                            direction: 'Chat',
                            from_number: 'Chat User',
                            to_number: chat.agent_name || 'AI Agent',
                            call_status: chat.status || 'completed',
                            type: 'chat' as const
                        }));
                        setList(res);
                    } else { // 'all'
                        const data = await getAllSessions(user_id);
                        const res = data.data.map((session: any, index: number) => {
                            if (session.type === 'call') {
                                return {
                                    ...session,
                                    id: `call_${index}`,
                                    name: session.Name?.name || session.name,
                                    duration_ms: formatDurationMillis(session.duration_ms),
                                    End_time: dateTime(session.End_time),
                                    type: 'call' as const
                                };
                            } else {
                                return {
                                    ...session,
                                    id: `chat_${index}`,
                                    name: session.customer_name,
                                    End_time: session.ended_at ? dateTime(session.ended_at) : 'Active',
                                    duration_ms: session.message_count ? `${session.message_count} messages` : '0 messages',
                                    direction: 'Chat',
                                    from_number: 'Chat User',
                                    to_number: session.agent_name || 'AI Agent',
                                    call_status: session.status || 'completed',
                                    type: 'chat' as const
                                };
                            }
                        });
                        setList(res);
                    }
                } catch (error) {
                    console.error("Error loading data:", error);
                    show("Error loading history data");
                } finally {
                    setLoading(false);
                }
            };
            
            loadData();
        }
    }, [viewMode]);

    const open = async (rowData: any) => {
        if (rowData.type === 'chat') {
            // Handle chat record - show chat-specific information
            setSideBarData({
                type: 'chat',
                transcript: `Chat Session Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session ID: ${rowData.session_id || 'Unknown'}
Customer: ${rowData.name || 'Unknown'}
Agent: ${rowData.agent_name || 'AI Agent'}
Messages: ${rowData.message_count || 0}
Started: ${rowData.started_at || 'Unknown'}
Ended: ${rowData.ended_at || 'Active'}
Status: ${rowData.status || 'Unknown'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This was a chat conversation between the customer and AI agent. 
Chat transcripts contain the full message history between participants.

Note: Full chat message history is not yet implemented in this view.`,
                summary: `Chat session with ${rowData.message_count || 0} messages between ${rowData.name || 'customer'} and ${rowData.agent_name || 'AI agent'}. Session ${rowData.status === 'active' ? 'is currently active' : 'has ended'}.`
            });
            
            setConversationEval(null);
            setEntityData(null);
            setAudioError("No audio recording available for chat sessions");
            setAudioSrc(undefined);
            setVisible(true);
            return;
        }
        
        // Handle call records (existing implementation)
        setSideBarData({
            type: 'call',
            recording_api: rowData.recording_api, 
            transcript: rowData.transcript, 
            summary: rowData.summary
        });
        
        // Reset states
        setConversationEval(null);
        setEntityData(null);
        setAudioError(null);
        setAudioSrc(undefined);
        setVisible(true);
        
        // Extract conversation_id from the recording_api URL
        let conversationId = null;
        if (rowData.recording_api) {
            const urlParts = rowData.recording_api.split('/');
            conversationId = urlParts[urlParts.length - 1];
            console.log("Extracted conversation ID:", conversationId);
        }
        
        // ALWAYS fetch call details regardless of audio availability
        if (conversationId) {
            try {
                const user_id = localStorage.getItem("fullName");
                if (user_id) {
                    setDetailsLoading(true);
                    const response = await getCallDetails(user_id, conversationId);
                    
                    if (response.status <= 299 && response.data) {
                        const callDetails: CallDetailsResponse = response.data;
                        
                        // Process conversation eval data
                        if (callDetails.conversation_eval) {
                            setConversationEval(callDetails.conversation_eval);
                        } else {
                            setConversationEval(null);
                        }
                        
                        // Process entity data
                        if (callDetails.entity) {
                            setEntityData(callDetails.entity);
                        } else {
                            setEntityData(null);
                        }
                        
                        // Update sidebar data with fresh transcript/summary if available
                        setSideBarData((prev: any) => ({
                            ...prev,
                            transcript: callDetails.transcription || prev?.transcript,
                            summary: callDetails.summary || prev?.summary
                        }));
                    } else {
                        setConversationEval(null);
                        setEntityData(null);
                    }
                }
            } catch (error) {
                console.error("Error fetching call details:", error);
                show("Error fetching call details", "info");
                setConversationEval(null);
                setEntityData(null);
            } finally {
                setDetailsLoading(false);
            }
        }
    };

    const lockTemplate = (rowData: any) => {
        return (
            <span className='view' onClick={() => open(rowData)}>
                View Details
                <i className="pi pi-arrow-up-right"></i>
            </span>
        );
    };

    // Clear all filters
    const clearFilters = () => {
        setSearchText('');
        setStartDate(null);
        setEndDate(null);
        setSelectedStatus('');
        setSelectedDirection('');
        setSelectedRecords([]);
    };

    // Toggle filters visibility
    const toggleFilters = () => {
        setShowFilters(!showFilters);
    };

    // Convert data to CSV format
    const convertToCSV = (data: HistoryRecord[]) => {
        const headers = ['Type', 'Name', 'Time', 'Duration', 'Type/Direction', 'From', 'To', 'Status'];
        const csvContent = [
            headers.join(','),
            ...data.map(record => [
                `"${record.type || ''}"`,
                `"${record.name || record.customer_name || ''}"`,
                `"${record.End_time || ''}"`,
                `"${record.duration_ms || ''}"`,
                `"${record.direction || ''}"`,
                `"${record.from_number || ''}"`,
                `"${record.to_number || ''}"`,
                `"${record.call_status || record.status || ''}"`
            ].join(','))
        ].join('\n');
        
        return csvContent;
    };

    // Download CSV
    const downloadCSV = () => {
        const dataToExport = selectedRecords.length > 0 ? selectedRecords : filteredList;
        
        if (dataToExport.length === 0) {
            show("No data to export", "info");
            return;
        }

        const csvContent = convertToCSV(dataToExport);
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `${viewMode}_history_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        show(`Exported ${dataToExport.length} records`, "success");
    };

    const header = (
        <div className="table-header">
            <div className="header-top">
                <ConditionalWrapper condition="call_history.view_mode_toggle">
                    <div className="view-mode-toggle">
                        <Button
                            label="Calls"
                            onClick={() => setViewMode('calls')}
                            outlined={viewMode !== 'calls'}
                            size="small"
                        />
                        <Button
                            label="Chats"
                            onClick={() => setViewMode('chats')}
                            outlined={viewMode !== 'chats'}
                            size="small"
                        />
                        <Button
                            label="All"
                            onClick={() => setViewMode('all')}
                            outlined={viewMode !== 'all'}
                            size="small"
                        />
                    </div>
                </ConditionalWrapper>
                
                <div className="header-actions">
                    <ConditionalWrapper condition="call_history.filters_section">
                        <Button
                            label="Filters"
                            icon={showFilters ? "pi pi-filter-slash" : "pi pi-filter"}
                            onClick={toggleFilters}
                            className="filter-toggle-btn"
                            size="small"
                            outlined
                        />
                        
                        {(searchText || startDate || endDate || selectedStatus || selectedDirection) && (
                            <Button
                                label="Clear All"
                                icon="pi pi-times"
                                onClick={clearFilters}
                                className="clear-all-btn"
                                size="small"
                                severity="secondary"
                                outlined
                            />
                        )}
                    </ConditionalWrapper>
                </div>
                
                <ConditionalWrapper condition="call_history.selection_checkboxes">
                    <div className="selection-info">
                        {selectedRecords.length > 0 && (
                            <span className="selected-count">
                                {selectedRecords.length} selected
                            </span>
                        )}
                        <span className="total-count">
                            Showing {filteredList.length} of {list.length} {viewMode === 'calls' ? 'calls' : viewMode === 'chats' ? 'chats' : 'sessions'}
                        </span>
                    </div>
                </ConditionalWrapper>
                
                <ConditionalWrapper condition="call_history.csv_download">
                    <Button
                        label={selectedRecords.length > 0 ? `Download Selected (${selectedRecords.length})` : `Download All (${filteredList.length})`}
                        icon="pi pi-download"
                        onClick={downloadCSV}
                        className="download-btn"
                        disabled={filteredList.length === 0}
                    />
                </ConditionalWrapper>
            </div>
            
            <ConditionalWrapper condition="call_history.filters_section">
                {showFilters && (
                    <div className="filter-section">
                        <ConditionalWrapper condition="call_history.search_functionality">
                            <div className="filter-row">
                                <div className="filter-item">
                                    <label>Search:</label>
                                    <InputText
                                        value={searchText}
                                        onChange={(e) => setSearchText(e.target.value)}
                                        placeholder="Search by name, number, or agent..."
                                        className="search-input"
                                    />
                                </div>
                                
                                <ConditionalWrapper condition="call_history.date_range_filter">
                                    <div className="filter-item">
                                        <label>From Date:</label>
                                        <Calendar
                                            value={startDate}
                                            onChange={(e) => setStartDate(e.value as Date)}
                                            placeholder="Start date"
                                            dateFormat="dd/mm/yy"
                                            showIcon
                                        />
                                    </div>
                                    
                                    <div className="filter-item">
                                        <label>To Date:</label>
                                        <Calendar
                                            value={endDate}
                                            onChange={(e) => setEndDate(e.value as Date)}
                                            placeholder="End date"
                                            dateFormat="dd/mm/yy"
                                            showIcon
                                        />
                                    </div>
                                </ConditionalWrapper>
                            </div>
                        </ConditionalWrapper>
                        
                        <div className="filter-row">
                            <ConditionalWrapper condition="call_history.status_filter">
                                <div className="filter-item">
                                    <label>Status:</label>
                                    <Dropdown
                                        value={selectedStatus}
                                        options={statusOptions}
                                        onChange={(e) => setSelectedStatus(e.value)}
                                        placeholder="Select status"
                                        className="status-dropdown"
                                    />
                                </div>
                            </ConditionalWrapper>
                            
                            <ConditionalWrapper condition="call_history.direction_filter">
                                <div className="filter-item">
                                    <label>Type:</label>
                                    <Dropdown
                                        value={selectedDirection}
                                        options={directionOptions}
                                        onChange={(e) => setSelectedDirection(e.value)}
                                        placeholder="Select type"
                                        className="direction-dropdown"
                                    />
                                </div>
                            </ConditionalWrapper>
                            
                            <div className="filter-spacer"></div>
                        </div>
                    </div>
                )}
            </ConditionalWrapper>
        </div>
    );

    // Custom column templates for better display
    const typeTemplate = (rowData: HistoryRecord) => {
        return (
            <span className={`type-badge ${rowData.type}`}>
                {rowData.type === 'call' ? '📞 Call' : '💬 Chat'}
            </span>
        );
    };

    const nameTemplate = (rowData: HistoryRecord) => {
        return rowData.name || rowData.customer_name || 'Unknown';
    };

    const statusTemplate = (rowData: HistoryRecord) => {
        const status = rowData.type === 'chat' ? rowData.status : rowData.call_status;
        return (
            <span className={`status-badge ${status?.toLowerCase()}`}>
                {status || 'Unknown'}
            </span>
        );
    };

    // Create conditional props for DataTable
    const dataTableProps = isSelectionEnabled
        ? {
            selection: selectedRecords,
            onSelectionChange: (e: DataTableSelectionMultipleChangeEvent<HistoryRecord[]>) => setSelectedRecords(e.value || []),
            selectionMode: "checkbox" as const,
          }
        : {};

    return (
        <div className="history">
            <Toast ref={toast} position="bottom-right" />
            <div className="card">
                <DataTable 
                    value={filteredList} 
                    tableStyle={{ minWidth: '80rem', maxHeight: '100rem', fontSize: '1.5rem' }} 
                    size='large' 
                    resizableColumns 
                    scrollable 
                    scrollHeight='65vh'
                    header={header}
                    dataKey="id"
                    paginator
                    rows={10}
                    rowsPerPageOptions={[5, 10, 25, 50]}
                    paginatorTemplate="FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink RowsPerPageDropdown"
                    currentPageReportTemplate="{first} to {last} of {totalRecords}"
                    {...dataTableProps}
                >
                    {isSelectionEnabled && (
                        <Column selectionMode="multiple" headerStyle={{ width: '3rem' }}></Column>
                    )}
                    <Column field="type" header="Type" body={typeTemplate} sortable style={{ width: '100px' }}></Column>
                    <Column field="name" header="Name" body={nameTemplate} sortable></Column>
                    <Column header="Time" field="End_time" sortable></Column>
                    <Column header="Duration" field="duration_ms" sortable></Column>
                    <Column header="Direction" field="direction" sortable></Column>
                    <Column header="From" field="from_number" sortable></Column>
                    <Column header="To" field="to_number" sortable></Column>
                    <Column header="Status" body={statusTemplate} sortable></Column>
                    <Column body={lockTemplate} header="Details"></Column>
                </DataTable>
            </div>
            
            <Sidebar 
                visible={visible} 
                onHide={() => setVisible(false)}
                position='right'
                className='sidebar'
            > 
                <h2>{sideBarData?.type === 'chat' ? 'Chat Details' : 'Recording/Transcript'}</h2>
                <div className='sidebar-text'>
                    {/* Audio Section - only for calls AND if audio is enabled in config */}
                    {sideBarData?.type === 'call' && (
                        <ConditionalWrapper condition="call_history.call_details_sidebar.audio_recording">
                            <div className='audio-section'>
                                <h3>Recording</h3>
                                {audioLoading && (
                                    <div className="audio-loading">
                                        <ScaleLoader height={20} width={2} radius={5} margin={2} color="#979797" />
                                        <p>Loading audio...</p>
                                    </div>
                                )}
                                
                                {audioError && (
                                    <div className="audio-error">
                                        <i className="pi pi-exclamation-triangle" style={{color: '#ff9800', marginRight: '8px'}}></i>
                                        <span style={{color: '#666', fontStyle: 'italic'}}>{audioError}</span>
                                    </div>
                                )}
                                
                                {audioSrc && !audioError && (
                                    <audio crossOrigin='anonymous' controls src={audioSrc} style={{width: '100%'}}></audio>
                                )}
                            </div>
                        </ConditionalWrapper>
                    )}
                    
                    {/* Chat info section - only for chats */}
                    {sideBarData?.type === 'chat' && (
                        <div className='chat-info-section'>
                            <h3>Session Information</h3>
                            <div className="chat-info-grid">
                                <div className="info-item">
                                    <span className="info-label">Type:</span>
                                    <span className="info-value">💬 Chat Session</span>
                                </div>
                                <div className="info-item">
                                    <span className="info-label">Audio:</span>
                                    <span className="info-value">Not available for chat sessions</span>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {/* Transcript Section - conditional */}
                    <ConditionalWrapper condition="call_history.call_details_sidebar.transcript_section">
                        <div className='transcript'>
                            <h3>{sideBarData?.type === 'chat' ? 'Chat Details' : 'Transcript'}</h3>
                            <p>
                                <pre>{sideBarData?.transcript || "Transcript not available"}</pre>  
                            </p>
                        </div>
                    </ConditionalWrapper>
                    
                    {/* Summary Section - conditional */}
                    <ConditionalWrapper condition="call_history.call_details_sidebar.summary_section">
                        <div className='summary'>
                            <h3>Summary</h3>
                            <p>
                                {sideBarData?.summary || "Summary not available"}
                            </p>
                        </div>
                    </ConditionalWrapper>
                    
                    {/* Conversation Evaluation - Only for calls and if enabled */}
                    {sideBarData?.type === 'call' && (
                        <ConditionalWrapper condition="call_history.call_details_sidebar.conversation_evaluation">
                            {detailsLoading ? (
                                <div className="details-loading">
                                    <ScaleLoader height={20} width={2} radius={5} margin={2} color="#979797" />
                                </div>
                            ) : (
                                <ConversationEval evalData={conversationEval} />
                            )}
                        </ConditionalWrapper>
                    )}
                    
                    {/* Entity Extraction - Only for calls and if enabled */}
                    {sideBarData?.type === 'call' && (
                        <ConditionalWrapper condition="call_history.call_details_sidebar.entity_extraction">
                            {detailsLoading ? (
                                <div className="details-loading">
                                    <ScaleLoader height={20} width={2} radius={5} margin={2} color="#979797" />
                                </div>
                            ) : (
                                <EntityExtraction entities={entityData} />
                            )}
                        </ConditionalWrapper>
                    )}
                    
                    {/* Chat-specific note */}
                    {sideBarData?.type === 'chat' && (
                        <div className='chat-note'>
                            <h3>📝 Note</h3>
                            <p>
                                Chat sessions don't have conversation evaluations or entity extractions like voice calls. 
                                The analysis focuses on message content and interaction patterns instead.
                            </p>
                        </div>
                    )}
                </div>
            </Sidebar>

            {loading && (
                <div className="loader-overlay">
                    <MoonLoader size={50} color="black" />
                </div>
            )}
        </div> 
    );
};

export default History;