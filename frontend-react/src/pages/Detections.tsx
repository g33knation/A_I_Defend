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
        matchesStatus = !(detection as any).feedback;
      } else if (selectedStatus !== 'all') {
        matchesStatus = (detection as any).feedback === selectedStatus;
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

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'confirmed_threat':
        return 'bg-red-100 text-red-800';
      case 'false_positive':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
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
    <div className="p-4 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Threat Detections</h1>
          <p className="text-sm text-gray-600 mt-0.5">{filteredDetections.length} detections</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              type="text"
              placeholder="Search..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
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
            className="px-4 py-2 text-base font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 transition-colors"
          >
            Purge All
          </button>
        </div>
      </div>

      {/* Detections Grid */}
      {paginatedDetections.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {paginatedDetections.map((detection: any) => (
            <div key={detection.id} className="bg-white rounded-lg border border-gray-200 p-2 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-1.5">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 text-xs mb-0.5 truncate">
                    {detection.summary || detection.type || 'Detection'}
                  </h3>
                  <p className="text-[10px] text-gray-500">{formatDate(detection.detected_at || detection.created_at)}</p>
                </div>
                <span className={`px-1 py-0.5 text-[10px] font-medium rounded-full shrink-0 ${getStatusBadgeClass(detection.feedback)}`}>
                  {getStatusLabel(detection.feedback)}
                </span>
              </div>

              {/* Detection details */}
              <div className="text-[10px] text-gray-600 space-y-0.5 mb-1.5">
                {detection.category && (
                  <div>
                    <span className="font-medium">Category:</span> {detection.category}
                  </div>
                )}
                {detection.score && (
                  <div>
                    <span className="font-medium">Threat Score:</span> {(detection.score * 100).toFixed(0)}%
                  </div>
                )}
              </div>

              {/* Details toggle */}
              <button
                onClick={() => toggleDetails(detection.id)}
                className="w-full flex items-center justify-between px-1.5 py-0.5 text-[10px] font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded transition-colors mb-1.5"
              >
                <span>Details</span>
                <svg
                  className={`w-2.5 h-2.5 transition-transform ${expandedDetections.has(detection.id) ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Expanded details */}
              {expandedDetections.has(detection.id) && (
                <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 text-[10px] space-y-1">
                  {detection.ai_output?.scanner && (
                    <div>
                      <span className="font-semibold">Scanner:</span> {detection.ai_output.scanner}
                    </div>
                  )}
                  {detection.ai_output?.target && (
                    <div className="truncate">
                      <span className="font-semibold">Target:</span> {detection.ai_output.target}
                    </div>
                  )}
                </div>
              )}

              {/* Feedback buttons */}
              {!detection.feedback && (
                <div className="flex gap-1">
                  <button
                    onClick={() => handleFeedback(detection.id, 'confirmed_threat')}
                    className="flex-1 px-1.5 py-0.5 text-[10px] font-medium rounded text-white bg-red-600 hover:bg-red-700 transition-colors"
                  >
                    Threat
                  </button>
                  <button
                    onClick={() => handleFeedback(detection.id, 'false_positive')}
                    className="flex-1 px-1.5 py-0.5 text-[10px] font-medium rounded text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors"
                  >
                    False
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="text-center py-8 bg-white rounded-lg border border-gray-200 max-w-sm mx-auto">
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No detections found</h3>
          <p className="mt-1 text-xs text-gray-500">
            {searchQuery || selectedStatus !== 'all' ? 'Try adjusting your search or filter' : 'No detections have been recorded yet'}
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <nav className="mt-6 flex items-center justify-between">
          <div className="text-base text-gray-700">
            Showing <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
            <span className="font-medium">{Math.min(currentPage * itemsPerPage, filteredDetections.length)}</span> of{' '}
            <span className="font-medium">{filteredDetections.length}</span> results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => changePage(currentPage - 1)}
              disabled={currentPage === 1}
              className={`px-4 py-2 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white transition-colors ${
                currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'
              }`}
            >
              Previous
            </button>
            <button
              onClick={() => changePage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className={`px-4 py-2 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white transition-colors ${
                currentPage >= totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'
              }`}
            >
              Next
            </button>
          </div>
        </nav>
      )}
    </div>
  );
}
