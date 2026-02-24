import { useState, useEffect, useMemo } from 'react';
import { useDefenseStore } from '../store/defenseStore';

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'new', label: 'New' },
  { value: 'confirmed_threat', label: 'Confirmed Threat' },
  { value: 'false_positive', label: 'False Positive' },
];

export default function Detections() {
  const { detections, fetchDetections, submitFeedback, purgeDetections } = useDefenseStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedDetections, setExpandedDetections] = useState<Set<string>>(new Set());
  const itemsPerPage = 10;

  useEffect(() => {
    fetchDetections();
  }, [fetchDetections]);

  const filteredDetections = useMemo(() => {
    return detections.filter((detection) => {
      const matchesSearch = JSON.stringify(detection).toLowerCase().includes(searchQuery.toLowerCase());
      let matchesStatus = true;
      if (selectedStatus === 'new') {
        matchesStatus = !detection.feedback;
      } else if (selectedStatus !== 'all') {
        matchesStatus = detection.feedback === selectedStatus;
      }
      return matchesSearch && matchesStatus;
    });
  }, [detections, searchQuery, selectedStatus]);

  const paginatedDetections = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredDetections.slice(start, end);
  }, [filteredDetections, currentPage]);

  const totalPages = Math.ceil(filteredDetections.length / itemsPerPage);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const changePage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const handleFeedback = async (detectionId: string, feedback: string) => {
    await submitFeedback(detectionId, feedback);
  };



  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'confirmed_threat':
        return 'Threat';
      case 'false_positive':
        return 'False Positive';
      default:
        return 'New';
    }
  };

  const toggleDetails = (detectionId: string) => {
    setExpandedDetections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(detectionId)) {
        newSet.delete(detectionId);
      } else {
        newSet.add(detectionId);
      }
      return newSet;
    });
  };

  return (
    <div className="p-4 max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Threat Detections</h1>
          <p className="text-sm text-slate-400 mt-0.5">{filteredDetections.length} detections pending review</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              type="text"
              placeholder="Search detections..."
              className="pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all w-64"
            />
            <svg className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all cursor-pointer"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-900 text-slate-200">
                {option.label}
              </option>
            ))}
          </select>
          <button
            onClick={async () => {
              if (window.confirm('Are you sure you want to delete ALL detections? This cannot be undone.')) {
                await purgeDetections();
              }
            }}
            className="px-4 py-2 text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 transition-colors shadow-lg shadow-red-500/20"
          >
            Purge All
          </button>
        </div>
      </div>

      {/* Detections Grid */}
      {paginatedDetections.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {paginatedDetections.map((detection: any) => {
            // Update badge class logic for dark mode inside mapping if needed, or rely on getStatusBadgeClass
            // But we need to update getStatusBadgeClass helper too or override it here with classes
            let badgeClass = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            if (detection.feedback === 'confirmed_threat') badgeClass = 'bg-red-500/10 text-red-400 border-red-500/20';
            if (detection.feedback === 'false_positive') badgeClass = 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';

            return (
              <div key={detection.id} className="glass p-4 rounded-xl hover:bg-slate-800/40 transition-all duration-300 group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0 mr-2">
                    <h3 className="font-semibold text-slate-200 text-sm mb-1 truncate group-hover:text-white transition-colors">
                      {detection.summary || detection.type || 'Detection'}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatDate(detection.detected_at || detection.created_at)}
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold rounded border ${badgeClass} shrink-0`}>
                    {getStatusLabel(detection.feedback)}
                  </span>
                </div>

                {/* Detection details */}
                <div className="space-y-1.5 pt-3 border-t border-slate-800/50 mb-3">
                  {detection.category && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Category:</span>
                      <span className="text-slate-300 capitalize">{detection.category}</span>
                    </div>
                  )}
                  {detection.score && (
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Threat Score:</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${detection.score > 0.7 ? 'bg-red-500' : detection.score > 0.4 ? 'bg-orange-500' : 'bg-blue-500'}`}
                            style={{ width: `${detection.score * 100}%` }}
                          />
                        </div>
                        <span className="text-slate-300 font-mono">{(detection.score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Details toggle */}
                <button
                  onClick={() => toggleDetails(detection.id)}
                  className="w-full flex items-center justify-between px-3 py-1.5 text-xs font-medium text-slate-400 bg-slate-900/50 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800/50 mb-3"
                >
                  <span>View Details</span>
                  <svg
                    className={`w-3 h-3 transition-transform ${expandedDetections.has(detection.id) ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Expanded details */}
                {expandedDetections.has(detection.id) && (
                  <div className="mb-3 p-3 bg-slate-950/50 rounded-lg border border-slate-800/50 text-xs text-slate-300 space-y-1.5 animate-in fade-in slide-in-from-top-1">
                    {detection.ai_output?.scanner && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Scanner:</span>
                        <span className="font-mono text-blue-400">{detection.ai_output.scanner}</span>
                      </div>
                    )}
                    {detection.ai_output?.target && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Target:</span>
                        <span className="font-mono truncate ml-2">{detection.ai_output.target}</span>
                      </div>
                    )}
                    {/* Raw output fallback if needed */}
                    {!detection.ai_output?.scanner && (
                      <pre className="overflow-x-auto text-[10px] text-slate-500 max-h-20">
                        {JSON.stringify(detection.ai_output, null, 2)}
                      </pre>
                    )}
                  </div>
                )}

                {/* Feedback buttons - Always visible so user can switch */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleFeedback(detection.id, 'confirmed_threat')}
                    className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${detection.feedback === 'confirmed_threat'
                        ? 'bg-red-600 text-white border-red-500 shadow-lg shadow-red-500/20'
                        : 'text-slate-400 bg-slate-900/50 hover:bg-slate-800 border border-slate-700/50'
                      }`}
                  >
                    Confirm Threat
                  </button>
                  <button
                    onClick={() => handleFeedback(detection.id, 'false_positive')}
                    className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${detection.feedback === 'false_positive'
                        ? 'bg-yellow-600/80 text-white border-yellow-500 shadow-lg shadow-yellow-500/20'
                        : 'text-slate-400 bg-slate-900/50 hover:bg-slate-800 border border-slate-700/50'
                      }`}
                  >
                    False Positive
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20 text-center glass rounded-xl">
          <div className="p-3 bg-slate-900/50 rounded-full mb-4">
            <svg className="h-8 w-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-200">No detections found</h3>
          <p className="mt-1 text-sm text-slate-500 max-w-xs mx-auto">
            {searchQuery || selectedStatus !== 'all'
              ? 'No detections match your filters.'
              : 'Clean slate! No threats have been detected yet.'}
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <div className="text-sm text-slate-400">
            Showing <span className="font-medium text-slate-300">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
            <span className="font-medium text-slate-300">{Math.min(currentPage * itemsPerPage, filteredDetections.length)}</span> of{' '}
            <span className="font-medium text-slate-300">{filteredDetections.length}</span> results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => changePage(currentPage - 1)}
              disabled={currentPage === 1}
              className={`px-4 py-2 border border-slate-700 text-sm font-medium rounded-lg transition-all ${currentPage === 1
                ? 'bg-slate-900/30 text-slate-600 border-slate-800 cursor-not-allowed'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-slate-600'
                }`}
            >
              Previous
            </button>
            <button
              onClick={() => changePage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className={`px-4 py-2 border border-slate-700 text-sm font-medium rounded-lg transition-all ${currentPage >= totalPages
                ? 'bg-slate-900/30 text-slate-600 border-slate-800 cursor-not-allowed'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white hover:border-slate-600'
                }`}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
