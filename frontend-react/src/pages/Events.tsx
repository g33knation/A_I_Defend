import { useState, useEffect, useMemo } from 'react';
import { useDefenseStore } from '../store/defenseStore';

export default function Events() {
  const { events, fetchEvents } = useDefenseStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const eventTypes = useMemo(() => {
    const types = new Set(events.map(event => event.type));
    return ['all', ...Array.from(types)];
  }, [events]);

  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      const matchesSearch = JSON.stringify(event).toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = selectedType === 'all' || event.type === selectedType;
      return matchesSearch && matchesType;
    });
  }, [events, searchQuery, selectedType]);

  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredEvents.slice(start, end);
  }, [filteredEvents, currentPage]);

  const totalPages = Math.ceil(filteredEvents.length / itemsPerPage);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const changePage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="p-4 max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security Events</h1>
          <p className="text-sm text-slate-400 mt-0.5">{filteredEvents.length} events recorded</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              type="text"
              placeholder="Search events..."
              className="pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all w-64"
            />
            <svg className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all cursor-pointer"
          >
            {eventTypes.map((type) => (
              <option key={type} value={type} className="bg-slate-900 text-slate-200">
                {type === 'all' ? 'All Types' : type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Events Grid */}
      {paginatedEvents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {paginatedEvents.map((event) => (
            <div
              key={event.id}
              className="glass p-4 rounded-xl hover:bg-slate-800/40 transition-all duration-300 group cursor-default"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0 mr-2">
                  <h3 className="font-semibold text-slate-200 text-sm mb-1 truncate group-hover:text-white transition-colors">
                    {event.type || 'Unknown Event'}
                  </h3>
                  <div className="flex items-center gap-1.5 text-xs text-slate-500">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatDate(event.created_at)}
                  </div>
                </div>
                <span className="px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 shrink-0">
                  {event.source || 'Unknown'}
                </span>
              </div>

              {/* Payload Details */}
              <div className="space-y-1.5 pt-3 border-t border-slate-800/50">
                {event.payload?.details?.address && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Target:</span>
                    <span className="text-slate-300 font-mono">{event.payload.details.address}</span>
                  </div>
                )}
                {event.payload?.details?.ports?.length ? (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Open Ports:</span>
                    <span className="text-slate-300 font-mono">{event.payload.details.ports.length}</span>
                  </div>
                ) : null}
                {event.payload?.severity && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Severity:</span>
                    <span className={`font-medium ${event.payload.severity === 'high' ? 'text-red-400' :
                        event.payload.severity === 'medium' ? 'text-orange-400' :
                          'text-slate-300'
                      }`}>
                      {event.payload.severity}
                    </span>
                  </div>
                )}
                {/* Fallback for minimal details */}
                {!event.payload?.details?.address && !event.payload?.details?.ports && (
                  <div className="text-xs text-slate-500 italic pb-1">
                    No additional details available
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20 text-center glass rounded-xl">
          <div className="p-3 bg-slate-900/50 rounded-full mb-4">
            <svg className="h-8 w-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-200">No events found</h3>
          <p className="mt-1 text-sm text-slate-500 max-w-xs mx-auto">
            {searchQuery || selectedType !== 'all'
              ? 'No events match your current filters. Try adjusting your search criteria.'
              : 'System appears quiet. No security events have been recorded yet.'}
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <div className="text-sm text-slate-400">
            Showing <span className="font-medium text-slate-300">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
            <span className="font-medium text-slate-300">{Math.min(currentPage * itemsPerPage, filteredEvents.length)}</span> of{' '}
            <span className="font-medium text-slate-300">{filteredEvents.length}</span> results
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
