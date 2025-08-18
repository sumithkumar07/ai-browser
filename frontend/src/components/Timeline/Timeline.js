import React, { useState, useEffect, useRef } from 'react';
import { ChevronDownIcon, ChevronUpIcon, ClockIcon, GlobeAltIcon, CpuChipIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

const Timeline = ({ isVisible, onClose, sessionId }) => {
  const [timelineData, setTimelineData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [sortOrder, setSortOrder] = useState('desc');
  const [groupBy, setGroupBy] = useState('time');
  const [searchTerm, setSearchTerm] = useState('');
  const timelineRef = useRef(null);

  useEffect(() => {
    if (isVisible) {
      fetchTimelineData();
    }
  }, [isVisible, sessionId, filter, sortOrder]);

  const fetchTimelineData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/timeline/entries?session_id=${sessionId}&filter=${filter}&sort=${sortOrder}`);
      if (response.ok) {
        const data = await response.json();
        setTimelineData(data.entries || []);
      }
    } catch (error) {
      console.error('Error fetching timeline data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEntryIcon = (type) => {
    switch (type) {
      case 'browse':
        return <GlobeAltIcon className="w-4 h-4" />;
      case 'chat':
        return <DocumentTextIcon className="w-4 h-4" />;
      case 'automation':
        return <CpuChipIcon className="w-4 h-4" />;
      default:
        return <ClockIcon className="w-4 h-4" />;
    }
  };

  const getEntryColor = (type) => {
    switch (type) {
      case 'browse':
        return 'bg-blue-500';
      case 'chat':
        return 'bg-green-500';
      case 'automation':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) {
      return 'Just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      return `${diffDays}d ago`;
    }
  };

  const groupEntries = (entries) => {
    if (groupBy === 'type') {
      const grouped = {};
      entries.forEach(entry => {
        if (!grouped[entry.type]) {
          grouped[entry.type] = [];
        }
        grouped[entry.type].push(entry);
      });
      return Object.entries(grouped).map(([type, items]) => ({
        group: type,
        entries: items
      }));
    } else {
      const grouped = {};
      entries.forEach(entry => {
        const date = new Date(entry.timestamp).toDateString();
        if (!grouped[date]) {
          grouped[date] = [];
        }
        grouped[date].push(entry);
      });
      return Object.entries(grouped).map(([date, items]) => ({
        group: date,
        entries: items
      }));
    }
  };

  const filteredEntries = timelineData.filter(entry => {
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return entry.data.title?.toLowerCase().includes(searchLower) ||
             entry.data.url?.toLowerCase().includes(searchLower) ||
             entry.data.message?.toLowerCase().includes(searchLower);
    }
    return true;
  });

  const groupedEntries = groupEntries(filteredEntries);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl border-l border-gray-200 z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Timeline</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <ChevronDownIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Controls */}
      <div className="p-4 border-b border-gray-200 space-y-3">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Search timeline..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-3 py-1 border border-gray-300 rounded-md text-sm"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="all">All Activities</option>
            <option value="browse">Browsing</option>
            <option value="chat">Chat</option>
            <option value="automation">Automation</option>
          </select>

          <select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value)}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="time">Group by Time</option>
            <option value="type">Group by Type</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="p-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
            title={`Sort ${sortOrder === 'desc' ? 'ascending' : 'descending'}`}
          >
            {sortOrder === 'desc' ? <ChevronDownIcon className="w-4 h-4" /> : <ChevronUpIcon className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Timeline Content */}
      <div className="flex-1 overflow-y-auto p-4" ref={timelineRef}>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          </div>
        ) : groupedEntries.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <ClockIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No timeline entries found</p>
          </div>
        ) : (
          <div className="space-y-6">
            {groupedEntries.map((group, groupIndex) => (
              <div key={groupIndex}>
                <h3 className="text-sm font-medium text-gray-700 mb-3 capitalize">
                  {group.group}
                </h3>
                <div className="relative">
                  {/* Timeline line */}
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
                  
                  <div className="space-y-4">
                    {group.entries.map((entry, index) => (
                      <TimelineEntry 
                        key={entry.entry_id} 
                        entry={entry} 
                        formatTime={formatTime}
                        getEntryIcon={getEntryIcon}
                        getEntryColor={getEntryColor}
                      />
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Smart Insights */}
      <TimelineInsights entries={timelineData} />
    </div>
  );
};

const TimelineEntry = ({ entry, formatTime, getEntryIcon, getEntryColor }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative pl-10">
      {/* Timeline dot */}
      <div className={`absolute left-3 w-2 h-2 rounded-full ${getEntryColor(entry.type)} -translate-x-1/2`}></div>
      
      <div className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-2 flex-1">
            <div className={`p-1.5 rounded ${getEntryColor(entry.type)} text-white`}>
              {getEntryIcon(entry.type)}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="font-medium text-sm text-gray-900">
                  {entry.data.title || entry.data.message || 'Activity'}
                </p>
                <span className="text-xs text-gray-500">
                  {formatTime(entry.timestamp)}
                </span>
              </div>
              
              {entry.data.url && (
                <p className="text-xs text-blue-600 truncate mt-1">
                  {entry.data.url}
                </p>
              )}
              
              {entry.ai_summary && (
                <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                  {entry.ai_summary}
                </p>
              )}

              {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                >
                  {expanded ? 'Show less' : 'Show details'}
                </button>
              )}

              {expanded && entry.metadata && (
                <div className="mt-2 p-2 bg-white rounded border text-xs">
                  <pre className="whitespace-pre-wrap text-gray-600">
                    {JSON.stringify(entry.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const TimelineInsights = ({ entries }) => {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    if (entries.length > 0) {
      generateInsights();
    }
  }, [entries]);

  const generateInsights = () => {
    const typeStats = {};
    const hourStats = {};
    let totalTime = 0;

    entries.forEach(entry => {
      typeStats[entry.type] = (typeStats[entry.type] || 0) + 1;
      
      const hour = new Date(entry.timestamp).getHours();
      hourStats[hour] = (hourStats[hour] || 0) + 1;
      
      if (entry.metadata?.duration) {
        totalTime += entry.metadata.duration;
      }
    });

    const mostActive = Object.entries(typeStats)
      .sort(([,a], [,b]) => b - a)[0];
    
    const peakHour = Object.entries(hourStats)
      .sort(([,a], [,b]) => b - a)[0];

    setInsights({
      totalActivities: entries.length,
      mostActiveType: mostActive?.[0],
      mostActiveCount: mostActive?.[1],
      peakHour: peakHour?.[0],
      totalTime: Math.round(totalTime / 60) // Convert to minutes
    });
  };

  if (!insights) return null;

  return (
    <div className="p-4 border-t border-gray-200 bg-gray-50">
      <h3 className="text-sm font-medium text-gray-700 mb-2">Smart Insights</h3>
      <div className="space-y-1 text-xs text-gray-600">
        <div className="flex justify-between">
          <span>Total Activities:</span>
          <span className="font-medium">{insights.totalActivities}</span>
        </div>
        
        {insights.mostActiveType && (
          <div className="flex justify-between">
            <span>Most Active:</span>
            <span className="font-medium capitalize">
              {insights.mostActiveType} ({insights.mostActiveCount})
            </span>
          </div>
        )}
        
        {insights.peakHour && (
          <div className="flex justify-between">
            <span>Peak Hour:</span>
            <span className="font-medium">{insights.peakHour}:00</span>
          </div>
        )}
        
        {insights.totalTime > 0 && (
          <div className="flex justify-between">
            <span>Total Time:</span>
            <span className="font-medium">{insights.totalTime}m</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default Timeline;