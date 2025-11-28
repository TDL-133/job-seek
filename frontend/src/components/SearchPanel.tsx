import { useState, useCallback } from 'react';
import { Search, Loader2, Check, AlertCircle, X } from 'lucide-react';

// Platform icons and names
const PLATFORMS = {
  linkedin: { name: 'LinkedIn', emoji: '💼' },
  indeed: { name: 'Indeed', emoji: '🔍' },
  glassdoor: { name: 'Glassdoor', emoji: '🚪' },
  welcometothejungle: { name: 'WTTJ', emoji: '🌴' },
};

type PlatformStatus = 'idle' | 'scanning' | 'complete' | 'error';

interface PlatformState {
  status: PlatformStatus;
  count: number;
  error?: string;
}

interface SearchPanelProps {
  onSearchComplete: () => void;
  defaultKeywords?: string;
  defaultLocation?: string;
}

export function SearchPanel({ 
  onSearchComplete, 
  defaultKeywords = '', 
  defaultLocation = '' 
}: SearchPanelProps) {
  const [keywords, setKeywords] = useState(defaultKeywords);
  const [location, setLocation] = useState(defaultLocation);
  const [isSearching, setIsSearching] = useState(false);
  const [platformStates, setPlatformStates] = useState<Record<string, PlatformState>>({});
  const [totalFound, setTotalFound] = useState<number | null>(null);
  
  const resetPlatformStates = () => {
    const initial: Record<string, PlatformState> = {};
    Object.keys(PLATFORMS).forEach(p => {
      initial[p] = { status: 'idle', count: 0 };
    });
    setPlatformStates(initial);
    setTotalFound(null);
  };
  
  const handleSearch = useCallback(async () => {
    if (!keywords.trim()) return;
    
    setIsSearching(true);
    resetPlatformStates();
    
    // Build URL with query params
    const params = new URLSearchParams({
      keywords: keywords.trim(),
      save_results: 'true',
    });
    if (location.trim()) {
      params.append('location', location.trim());
    }
    
    // Use relative URL to go through nginx proxy, or direct URL for dev
    const url = `/api/search/jobs/stream?${params.toString()}`;
    
    try {
      const eventSource = new EventSource(url);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.event) {
            case 'scanning_start':
              setPlatformStates(prev => ({
                ...prev,
                [data.platform]: { status: 'scanning', count: 0 }
              }));
              break;
              
            case 'scanning_complete':
              setPlatformStates(prev => ({
                ...prev,
                [data.platform]: { status: 'complete', count: data.count }
              }));
              break;
              
            case 'error':
              setPlatformStates(prev => ({
                ...prev,
                [data.platform]: { status: 'error', count: 0, error: data.message }
              }));
              break;
              
            case 'search_complete':
              setTotalFound(data.total);
              setIsSearching(false);
              eventSource.close();
              // Notify parent to refresh job list
              onSearchComplete();
              break;
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e);
        }
      };
      
      eventSource.onerror = () => {
        console.error('EventSource error');
        eventSource.close();
        setIsSearching(false);
      };
      
    } catch (error) {
      console.error('Search error:', error);
      setIsSearching(false);
    }
  }, [keywords, location, onSearchComplete]);
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isSearching) {
      handleSearch();
    }
  };
  
  const getPlatformIcon = (status: PlatformStatus) => {
    switch (status) {
      case 'scanning':
        return <Loader2 className="h-4 w-4 animate-spin text-primary-600" />;
      case 'complete':
        return <Check className="h-4 w-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <span className="h-4 w-4 rounded-full bg-neutral-200" />;
    }
  };
  
  const hasSearched = Object.values(platformStates).some(s => s.status !== 'idle');
  
  return (
    <div className="card">
      <div className="space-y-4">
        {/* Search inputs */}
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              🔍 Mots-clés
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Product Manager, Software Engineer..."
              className="input-field w-full"
              disabled={isSearching}
            />
          </div>
          
          <div className="flex-1">
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              📍 Ville
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paris, Lyon, Remote..."
              className="input-field w-full"
              disabled={isSearching}
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={handleSearch}
              disabled={isSearching || !keywords.trim()}
              className="btn-primary w-full md:w-auto flex items-center justify-center gap-2"
            >
              {isSearching ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Recherche...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Rechercher
                </>
              )}
            </button>
          </div>
        </div>
        
        {/* Platform status indicators */}
        {hasSearched && (
          <div className="pt-3 border-t border-neutral-100">
            <div className="flex flex-wrap gap-3">
              {Object.entries(PLATFORMS).map(([key, { name, emoji }]) => {
                const state = platformStates[key] || { status: 'idle', count: 0 };
                
                return (
                  <div
                    key={key}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                      state.status === 'complete' ? 'bg-green-50 text-green-800' :
                      state.status === 'scanning' ? 'bg-primary-50 text-primary-800' :
                      state.status === 'error' ? 'bg-red-50 text-red-800' :
                      'bg-neutral-50 text-neutral-600'
                    }`}
                  >
                    {getPlatformIcon(state.status)}
                    <span>{emoji} {name}</span>
                    {state.status === 'complete' && (
                      <span className="font-medium">{state.count}</span>
                    )}
                    {state.status === 'error' && (
                      <X className="h-3 w-3" />
                    )}
                  </div>
                );
              })}
            </div>
            
            {/* Total found */}
            {totalFound !== null && (
              <div className="mt-3 text-sm text-neutral-600">
                ✅ <span className="font-medium">{totalFound}</span> offre{totalFound > 1 ? 's' : ''} trouvée{totalFound > 1 ? 's' : ''} au total
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
