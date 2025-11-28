import { useState, useEffect } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { api } from '../services/api';
import type { Job, ScoredJob } from '../types';
import { 
  Loader2, Search, MapPin, Building2, Clock, ExternalLink, 
  FileText, Ban, ChevronDown, Sparkles 
} from 'lucide-react';

export default function Dashboard() {
  const [jobs, setJobs] = useState<ScoredJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  
  // Search filters
  const [keywords, setKeywords] = useState('');
  const [location, setLocation] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  
  // Cover letter modal
  const [selectedJob, setSelectedJob] = useState<ScoredJob | null>(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState(false);
  
  useEffect(() => {
    loadJobs();
  }, []);
  
  const loadJobs = async () => {
    try {
      const data = await api.jobs.list();
      // Score the jobs
      const scoredJobs = await Promise.all(
        data.slice(0, 20).map(async (job: Job) => {
          try {
            const result = await api.scoring.scoreJob(job.id);
            return { ...job, score: result.score, score_breakdown: result.breakdown };
          } catch {
            return { ...job, score: 0, score_breakdown: {} };
          }
        })
      );
      setJobs(scoredJobs.sort((a, b) => b.score - a.score));
    } catch (err: any) {
      setError('Erreur lors du chargement des offres');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearch = async () => {
    if (!keywords.trim()) return;
    
    setSearching(true);
    setError('');
    
    try {
      const data = await api.search.search({
        keywords: keywords.trim(),
        location: location.trim() || undefined,
        remote_only: remoteOnly,
      });
      
      // Score the results
      const scoredJobs = await Promise.all(
        data.slice(0, 20).map(async (job: Job) => {
          try {
            const result = await api.scoring.scoreJob(job.id);
            return { ...job, score: result.score, score_breakdown: result.breakdown };
          } catch {
            return { ...job, score: 0, score_breakdown: {} };
          }
        })
      );
      setJobs(scoredJobs.sort((a, b) => b.score - a.score));
    } catch (err: any) {
      setError('Erreur lors de la recherche');
    } finally {
      setSearching(false);
    }
  };
  
  const handleGenerateCoverLetter = async (job: ScoredJob) => {
    setSelectedJob(job);
    setGeneratingCoverLetter(true);
    setCoverLetter('');
    
    try {
      const result = await api.coverLetter.generate(job.id);
      setCoverLetter(result.cover_letter);
    } catch (err: any) {
      setCoverLetter('Erreur lors de la génération de la lettre de motivation.');
    } finally {
      setGeneratingCoverLetter(false);
    }
  };
  
  const handleBlacklistCompany = async (job: ScoredJob) => {
    if (!job.company) return;
    
    try {
      await api.blacklist.add({ company_name: job.company, reason: 'Blacklisté depuis le dashboard' });
      // Remove jobs from this company from the list
      setJobs(jobs.filter(j => j.company !== job.company));
    } catch (err) {
      setError('Erreur lors du blacklist');
    }
  };
  
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-primary-600 bg-primary-100';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-neutral-600 bg-neutral-100';
  };
  
  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Dashboard</h1>
          <p className="text-neutral-600">Découvre les offres qui matchent avec ton profil.</p>
        </div>
        
        {/* Search bar */}
        <div className="card">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-400" />
                <input
                  type="text"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Développeur, Designer, Marketing..."
                  className="input pl-10"
                />
              </div>
            </div>
            <div className="w-full md:w-48">
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-400" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ville..."
                  className="input pl-10"
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-neutral-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={remoteOnly}
                  onChange={(e) => setRemoteOnly(e.target.checked)}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                Remote
              </label>
              <button
                onClick={handleSearch}
                disabled={searching || !keywords.trim()}
                className="btn-primary"
              >
                {searching ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  'Rechercher'
                )}
              </button>
            </div>
          </div>
        </div>
        
        {error && (
          <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        )}
        
        {/* Results */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="card text-center py-12">
            <Sparkles className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">Aucune offre trouvée</h3>
            <p className="text-neutral-600">Lance une recherche pour découvrir des offres.</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-600">
                {jobs.length} offre{jobs.length > 1 ? 's' : ''} trouvée{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
            
            {jobs.map((job) => (
              <div key={job.id} className="card hover:shadow-md transition-shadow">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  {/* Score */}
                  <div className="lg:w-20 flex lg:flex-col items-center gap-2 lg:gap-1">
                    <div className={`w-14 h-14 rounded-xl flex items-center justify-center font-bold text-xl ${getScoreColor(job.score)}`}>
                      {Math.round(job.score)}
                    </div>
                    <span className="text-xs text-neutral-500">Match</span>
                  </div>
                  
                  {/* Job info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-semibold text-neutral-900 hover:text-primary-600 cursor-pointer">
                          {job.title}
                        </h3>
                        <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-neutral-600">
                          {job.company && (
                            <span className="flex items-center gap-1">
                              <Building2 className="h-4 w-4" />
                              {job.company}
                            </span>
                          )}
                          {job.location && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-4 w-4" />
                              {job.location}
                            </span>
                          )}
                          {job.posted_date && (
                            <span className="flex items-center gap-1">
                              <Clock className="h-4 w-4" />
                              {new Date(job.posted_date).toLocaleDateString('fr-FR')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {job.description && (
                      <p className="mt-2 text-sm text-neutral-600 line-clamp-2">
                        {job.description}
                      </p>
                    )}
                    
                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mt-3">
                      {job.remote && (
                        <span className="badge-success">Remote</span>
                      )}
                      {job.contract_type && (
                        <span className="badge-neutral">{job.contract_type}</span>
                      )}
                      {job.salary_min && job.salary_max && (
                        <span className="badge-neutral">
                          {job.salary_min.toLocaleString()}€ - {job.salary_max.toLocaleString()}€
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex lg:flex-col gap-2 lg:w-auto">
                    {job.url && (
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary text-sm"
                      >
                        <ExternalLink className="h-4 w-4 mr-1" />
                        Voir
                      </a>
                    )}
                    <button
                      onClick={() => handleGenerateCoverLetter(job)}
                      className="btn-secondary text-sm"
                    >
                      <FileText className="h-4 w-4 mr-1" />
                      Lettre
                    </button>
                    <button
                      onClick={() => handleBlacklistCompany(job)}
                      className="btn-ghost text-sm text-neutral-500 hover:text-red-600"
                      title="Blacklister cette entreprise"
                    >
                      <Ban className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                {/* Score breakdown */}
                {job.score_breakdown && Object.keys(job.score_breakdown).length > 0 && (
                  <details className="mt-4 pt-4 border-t border-neutral-100">
                    <summary className="text-sm text-neutral-600 cursor-pointer flex items-center gap-1">
                      <ChevronDown className="h-4 w-4" />
                      Détail du score
                    </summary>
                    <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                      {Object.entries(job.score_breakdown).map(([key, value]) => (
                        <div key={key} className="text-xs">
                          <span className="text-neutral-500 capitalize">{key.replace('_', ' ')}:</span>
                          <span className="ml-1 font-medium">{Math.round(value as number)}%</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Cover letter modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-neutral-200">
              <h3 className="text-lg font-semibold text-neutral-900">
                Lettre de motivation
              </h3>
              <p className="text-sm text-neutral-600">
                Pour: {selectedJob.title} chez {selectedJob.company}
              </p>
            </div>
            <div className="p-6 overflow-y-auto max-h-[50vh]">
              {generatingCoverLetter ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary-600 mb-4" />
                  <p className="text-neutral-600">Génération en cours...</p>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm text-neutral-700 bg-neutral-50 p-4 rounded-lg">
                    {coverLetter}
                  </pre>
                </div>
              )}
            </div>
            <div className="p-6 border-t border-neutral-200 flex justify-end gap-3">
              <button
                onClick={() => setSelectedJob(null)}
                className="btn-secondary"
              >
                Fermer
              </button>
              {coverLetter && (
                <button
                  onClick={() => navigator.clipboard.writeText(coverLetter)}
                  className="btn-primary"
                >
                  Copier
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
