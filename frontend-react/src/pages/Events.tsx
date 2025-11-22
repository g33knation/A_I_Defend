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
    <div className="p-4 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Security Events</h1>
          <p className="text-sm text-gray-600 mt-0.5">{filteredEvents.length} events</p>
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
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Events Grid */}
      {paginatedEvents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {paginatedEvents.map((event) => (
            <div
              key={event.id}
              className="bg-white rounded-lg border border-gray-200 p-2 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between mb-1.5">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 text-xs mb-0.5 truncate">
                    {event.type || 'Unknown Event'}
                  </h3>
                  <p className="text-[10px] text-gray-500">{formatDate(event.created_at)}</p>
                </div>
                <span className="px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-blue-100 text-blue-800 shrink-0">
                  {event.source || 'Unknown'}
                </span>
              </div>

              {/* Compact payload summary */}
              <div className="text-[10px] text-gray-600 space-y-0.5">
                {event.payload?.details?.address && (
                  <div className="truncate">
                    <span className="font-medium">Target:</span> {event.payload.details.address}
                  </div>
                )}
                {event.payload?.details?.ports?.length && (
                  <div>
                    <span className="font-medium">Ports:</span> {event.payload.details.ports.length}
                  </div>
                )}
                {event.payload?.severity && (
                  <div>
                    <span className="font-medium">Severity:</span> {event.payload.severity}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="text-center py-8 bg-white rounded-lg border border-gray-200 max-w-sm mx-auto">
          <svg className="mx-auto h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
          </svg>
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No events found</h3>
          <p className="mt-1 text-xs text-gray-500">
            {searchQuery || selectedType !== 'all' ? 'Try adjusting your search or filter' : 'No events have been recorded yet'}
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <nav className="mt-6 flex items-center justify-between">
          <div className="text-base text-gray-700">
            Showing <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> to{' '}
            <span className="font-medium">{Math.min(currentPage * itemsPerPage, filteredEvents.length)}</span> of{' '}
            <span className="font-medium">{filteredEvents.length}</span> results
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
