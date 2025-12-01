import { useState, useCallback, useEffect, useRef } from 'react';
import { Search, Loader2, RefreshCw, ArrowRight } from 'lucide-react';
import { savedSearchesApi } from '../services/api';

interface SearchPanelProps {
  onSearchComplete: (jobs?: any[]) => void;
  defaultKeywords?: string;
  defaultLocation?: string;
}

interface FindAllProgress {
  status: string;
  generated: number;
  matched: number;
  elapsed: number;
}

interface ActiveSearch {
  findallId: string;
  keywords: string;
  location: string;
  startedAt: number;
}

const ACTIVE_SEARCH_KEY = 'jobseek_active_findall';

export function SearchPanel({ 
  onSearchComplete, 
  defaultKeywords = '', 
  defaultLocation = '' 
}: SearchPanelProps) {
  const [keywords, setKeywords] = useState(defaultKeywords);
  const [location, setLocation] = useState(defaultLocation);
  const [isSearching, setIsSearching] = useState(false);
  const [progress, setProgress] = useState<FindAllProgress | null>(null);
  const [totalFound, setTotalFound] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // FindAll run tracking
  const [currentFindAllId, setCurrentFindAllId] = useState<string | null>(null);
  const [activeSearch, setActiveSearch] = useState<ActiveSearch | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Load active search from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(ACTIVE_SEARCH_KEY);
    if (stored) {
      try {
        const search = JSON.parse(stored) as ActiveSearch;
        // Check if search is less than 30 minutes old
        if (Date.now() - search.startedAt < 30 * 60 * 1000) {
          setActiveSearch(search);
          setKeywords(search.keywords);
          setLocation(search.location);
        } else {
          localStorage.removeItem(ACTIVE_SEARCH_KEY);
        }
      } catch (e) {
        localStorage.removeItem(ACTIVE_SEARCH_KEY);
      }
    }
  }, []);
  
  // Update keywords/location when props change (e.g., URL navigation)
  useEffect(() => {
    if (defaultKeywords) setKeywords(defaultKeywords);
    if (defaultLocation) setLocation(defaultLocation);
  }, [defaultKeywords, defaultLocation]);
  
  // Poll for status when there's an active search but no SSE connection
  const pollStatus = useCallback(async (findallId: string, search: ActiveSearch | null) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/search/status/${findallId}?token=${token}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'completed') {
          // Search completed - mark for resume
          localStorage.removeItem(ACTIVE_SEARCH_KEY);
          setActiveSearch(null);
          setProgress(null);
          if (pollingRef.current) clearInterval(pollingRef.current);
          // Set flag to show "Resume" button
          setCurrentFindAllId(findallId);
          setError(`Recherche terminée! ${data.matched_count} offres trouvées. Cliquez pour voir les résultats.`);
        } else if (data.status === 'failed' || data.status === 'cancelled') {
          localStorage.removeItem(ACTIVE_SEARCH_KEY);
          setActiveSearch(null);
          setProgress(null);
          if (pollingRef.current) clearInterval(pollingRef.current);
        } else {
          // Still running - update progress
          setProgress({
            status: data.status === 'running' ? 'Recherche en cours' : data.status,
            generated: data.generated_count || 0,
            matched: data.matched_count || 0,
            elapsed: Math.floor((Date.now() - (search?.startedAt || Date.now())) / 1000)
          });
        }
      }
    } catch (e) {
      console.error('Error polling status:', e);
    }
  }, []);
  
  // Start polling when there's an active search
  useEffect(() => {
    if (activeSearch && !isSearching) {
      // Initial poll
      pollStatus(activeSearch.findallId, activeSearch);
      // Set up interval
      pollingRef.current = setInterval(() => pollStatus(activeSearch.findallId, activeSearch), 5000);
      return () => {
        if (pollingRef.current) clearInterval(pollingRef.current);
      };
    }
  }, [activeSearch, isSearching, pollStatus]);
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  const handleSearch = useCallback(async (resumeId?: string) => {
    if (!resumeId && (!keywords.trim() || !location.trim())) return;
    
    setIsSearching(true);
    setProgress(null);
    setTotalFound(null);
    setError(null);
    
    // Auto-save search when starting (not resuming)
    if (!resumeId && keywords.trim() && location.trim()) {
      try {
        await savedSearchesApi.save({
          name: `${keywords.trim()} - ${location.trim()}`,
          keywords: keywords.trim(),
          location: location.trim()
        });
      } catch (err) {
        console.error('Failed to auto-save search:', err);
      }
    }
    
    // Build URL with query params
    const params = new URLSearchParams({
      keywords: keywords.trim() || 'Product Manager',
      location: location.trim() || 'Lille',
    });
    
    // Add auth token to URL for SSE (EventSource doesn't support headers)
    const token = localStorage.getItem('access_token');
    if (token) {
      params.append('token', token);
    }
    
    // Add resume ID if provided
    if (resumeId) {
      params.append('resume_id', resumeId);
    }
    
    const url = `/api/search/stream?${params.toString()}`;
    
    try {
      const eventSource = new EventSource(url);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.event) {
            case 'findall_created': {
              setCurrentFindAllId(data.findall_id);
              setProgress({ status: 'Démarrage...', generated: 0, matched: 0, elapsed: 0 });
              // Store in localStorage
              const newSearch: ActiveSearch = {
                findallId: data.findall_id,
                keywords: keywords.trim(),
                location: location.trim(),
                startedAt: Date.now()
              };
              localStorage.setItem(ACTIVE_SEARCH_KEY, JSON.stringify(newSearch));
              setActiveSearch(newSearch);
              break;
            }
              
            case 'findall_resumed':
              setCurrentFindAllId(data.findall_id);
              setProgress({ status: 'Reprise en cours...', generated: 0, matched: 0, elapsed: 0 });
              break;
              
            case 'findall_progress':
              setProgress({
                status: data.status === 'running' ? 'Recherche en cours' : data.status,
                generated: data.generated_count || 0,
                matched: data.matched_count || 0,
                elapsed: data.elapsed || 0
              });
              break;
              
            case 'findall_complete':
              setTotalFound(data.total_matched);
              setProgress(null);
              setIsSearching(false);
              setCurrentFindAllId(null);
              // Clear localStorage
              localStorage.removeItem(ACTIVE_SEARCH_KEY);
              setActiveSearch(null);
              eventSource.close();
              // Pass scored jobs to parent
              onSearchComplete(data.jobs || []);
              break;
              
            case 'error':
              setError(data.message || 'Erreur lors de la recherche');
              setProgress(null);
              setIsSearching(false);
              eventSource.close();
              break;
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e);
        }
      };
      
      eventSource.onerror = () => {
        console.error('EventSource error - attempting to continue tracking...');
        eventSource.close();
        
        // If we have a findall_id, offer to resume
        if (currentFindAllId) {
          setError(`Connexion perdue. La recherche continue en arrière-plan (ID: ${currentFindAllId.slice(-8)}). Cliquez sur "Reprendre" pour suivre la progression.`);
        } else {
          setError('Connexion perdue. Veuillez réessayer.');
        }
        setProgress(null);
        setIsSearching(false);
      };
      
    } catch (err) {
      console.error('Search error:', err);
      setError('Erreur lors de la recherche');
      setIsSearching(false);
    }
  }, [keywords, location, onSearchComplete]);
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isSearching && keywords.trim() && location.trim()) {
      handleSearch();
    }
  };
  
  return (
    <div className="bg-white rounded-xl shadow-lg border border-neutral-100 p-6">
      <div className="space-y-4">
        {/* Title */}
        <h2 className="text-lg font-semibold text-neutral-800 mb-2">🔎 Nouvelle recherche</h2>
        
        {/* Search inputs */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-neutral-600 mb-2">
              Intitulé du poste
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ex: Product Manager, Data Analyst..."
              className="input-field w-full text-base"
              disabled={isSearching}
            />
          </div>
          
          <div className="flex-1">
            <label className="block text-sm font-semibold text-neutral-600 mb-2">
              Ville
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ex: Paris, Lyon, Toulouse..."
              className="input-field w-full text-base"
              disabled={isSearching}
            />
          </div>
          
          <div className="flex items-end">
            {/* Search button */}
            <button
              onClick={() => handleSearch()}
              disabled={isSearching || !keywords.trim() || !location.trim()}
              className="btn-primary h-12 px-6 w-full md:w-auto flex items-center justify-center gap-2 text-base"
            >
              {isSearching ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Recherche...
                </>
              ) : (
                <>
                  <Search className="h-5 w-5" />
                  Lancer la recherche
                </>
              )}
            </button>
          </div>
        </div>
        
        
        {/* Progress Panel */}
        {progress && (
          <div className="bg-primary-50 rounded-lg p-4 border border-primary-100">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
                <span className="font-medium text-primary-900">
                  {progress.status}
                </span>
              </div>
              <span className="text-sm font-mono text-primary-700 bg-primary-100 px-2 py-1 rounded">
                {formatTime(progress.elapsed)}
              </span>
            </div>
            
            {/* Animated waiting bar */}
            <div className="mb-4">
              <div className="h-2 bg-primary-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary-500 rounded-full animate-pulse"
                  style={{ 
                    width: `${Math.min(95, (progress.elapsed / (20 * 60)) * 100)}%`,
                    transition: 'width 1s ease-out'
                  }}
                />
              </div>
            </div>
            
            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-neutral-700">
                  {progress.generated}
                </div>
                <div className="text-xs text-neutral-500">Candidats générés</div>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-600">
                  {progress.matched}
                </div>
                <div className="text-xs text-neutral-500">Offres matchées</div>
              </div>
            </div>
            
            {/* Waiting message with animation */}
            <div className="mt-4 p-3 bg-white rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <div className="text-sm text-neutral-600">
                  {progress.elapsed < 60 
                    ? "Démarrage de la recherche approfondie..."
                    : progress.elapsed < 300
                    ? "Analyse des offres sur Glassdoor, Indeed, LinkedIn, WTTJ..."
                    : progress.elapsed < 600
                    ? "Extraction des détails des offres trouvées..."
                    : progress.elapsed < 900
                    ? "Vérification et scoring des offres..."
                    : "Finalisation en cours, presque terminé..."}
                </div>
              </div>
            </div>
            
            {/* Estimated time */}
            <div className="mt-3 text-xs text-primary-600 text-center">
              ⏱️ Temps estimé restant: ~{Math.max(1, 15 - Math.floor(progress.elapsed / 60))} minutes
              <span className="ml-2 text-neutral-400">| Ne fermez pas cette page</span>
            </div>
          </div>
        )}
        
        {/* Success message */}
        {totalFound !== null && !isSearching && (
          <div className="bg-green-50 rounded-lg p-4 border border-green-100">
            <div className="flex items-center gap-2 text-green-800">
              <span className="text-xl">✅</span>
              <span className="font-medium">
                {totalFound} offre{totalFound > 1 ? 's' : ''} trouvée{totalFound > 1 ? 's' : ''}
              </span>
            </div>
          </div>
        )}
        
        {/* Success message from completed background search */}
        {error && error.includes('terminée') && currentFindAllId && (
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-green-800">
                <span className="text-xl">✅</span>
                <span>{error}</span>
              </div>
              <button
                onClick={() => {
                  setError(null);
                  handleSearch(currentFindAllId);
                }}
                className="btn-primary text-sm px-3 py-1 flex items-center gap-1"
              >
                Voir les résultats <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
        
        {/* Error message with resume option */}
        {error && !error.includes('terminée') && (
          <div className="bg-red-50 rounded-lg p-4 border border-red-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-800">
                <span className="text-xl">❌</span>
                <span>{error}</span>
              </div>
              {currentFindAllId && (
                <button
                  onClick={() => {
                    setError(null);
                    handleSearch(currentFindAllId);
                  }}
                  className="btn-primary text-sm px-3 py-1 flex items-center gap-1"
                >
                  <RefreshCw className="h-4 w-4" /> Reprendre
                </button>
              )}
            </div>
          </div>
        )}
        
      </div>
    </div>
  );
}
