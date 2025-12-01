import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { scoredJobsApi, type ScoredJob, type ScoreBreakdown } from '../services/api';
import { 
  Loader2, MapPin, Clock, ExternalLink, 
  ChevronDown, ChevronUp, Sparkles,
  Briefcase, Ban, Heart, Check
} from 'lucide-react';
import { api, applicationsApi } from '../services/api';
import { SearchPanel } from '../components/SearchPanel';

// Score breakdown component
function ScoreBreakdownPanel({ breakdown }: { breakdown: ScoreBreakdown }) {
  const categories = [
    { 
      key: 'role', 
      label: 'Role', 
      emoji: '🎭', 
      color: 'primary',
      data: breakdown.role 
    },
    { 
      key: 'geography', 
      label: 'Géo', 
      emoji: '🌍', 
      color: 'blue',
      data: breakdown.geography 
    },
    { 
      key: 'salary', 
      label: 'Salaire', 
      emoji: '💰', 
      color: 'green',
      data: breakdown.salary 
    },
    { 
      key: 'skills', 
      label: 'Skills', 
      emoji: '🎯', 
      color: 'purple',
      data: breakdown.skills 
    },
    { 
      key: 'attractiveness', 
      label: 'Attractivité', 
      emoji: '✨', 
      color: 'amber',
      data: breakdown.attractiveness 
    },
    { 
      key: 'penalties', 
      label: 'Pénalités', 
      emoji: '⚠️', 
      color: 'red',
      data: breakdown.penalties 
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {categories.map(({ key, label, emoji, data }) => {
        const isPenalty = key === 'penalties';
        const percentage = isPenalty 
          ? Math.abs(data.points) / Math.abs(data.max) * 100
          : (data.points / data.max) * 100;
        
        return (
          <div 
            key={key} 
            className={`p-3 rounded-lg ${isPenalty && data.points < 0 ? 'bg-red-50' : 'bg-neutral-50'}`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm">{emoji} {label}</span>
              <span className={`text-sm font-bold ${
                isPenalty && data.points < 0 ? 'text-red-600' :
                percentage >= 80 ? 'text-green-600' :
                percentage >= 50 ? 'text-blue-600' :
                'text-neutral-600'
              }`}>
                {data.points}/{data.max}
              </span>
            </div>
            
            {/* Progress bar */}
            <div className="h-1.5 bg-neutral-200 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full ${
                  isPenalty && data.points < 0 ? 'bg-red-500' :
                  percentage >= 80 ? 'bg-green-500' :
                  percentage >= 50 ? 'bg-blue-500' :
                  'bg-neutral-400'
                }`}
                style={{ width: `${Math.min(100, percentage)}%` }}
              />
            </div>
            
            {/* Details */}
            <p className="text-xs text-neutral-500 mt-1 truncate" title={data.details}>
              {data.details}
            </p>
          </div>
        );
      })}
    </div>
  );
}

// Clean location string
const cleanLocation = (location: string | null | undefined): string => {
  if (!location) return 'Non spécifié';
  // Remove GPS coordinates like "50.62920, 3.05726" or "; 50.5667, 3.0667"
  let cleaned = location.replace(/;?\s*\d+\.\d+,\s*\d+\.\d+/g, '');
  // Remove "NA, NA" patterns
  cleaned = cleaned.replace(/,?\s*NA,?\s*NA/g, '');
  // Remove trailing commas, semicolons and whitespace
  cleaned = cleaned.replace(/[,;\s]+$/g, '').trim();
  // Remove leading commas, semicolons
  cleaned = cleaned.replace(/^[,;\s]+/g, '').trim();
  // If nothing left, return default
  return cleaned || 'Non spécifié';
};

export default function DashboardV2() {
  const [searchParams] = useSearchParams();
  const [jobs, setJobs] = useState<ScoredJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // URL query params for saved search navigation
  const urlKeywords = searchParams.get('keywords') || '';
  const urlLocation = searchParams.get('location') || '';
  
  // Location filter from URL (active when coming from saved search)
  const [locationFilter, setLocationFilter] = useState<string>(urlLocation);
  
  // Update location filter when URL changes
  useEffect(() => {
    setLocationFilter(urlLocation);
  }, [urlLocation]);
  
  // Filters
  const [minScore, setMinScore] = useState<number>(0);
  const [expandedJob, setExpandedJob] = useState<number | null>(null);
  
  // Cover letter
  const [selectedJob, setSelectedJob] = useState<ScoredJob | null>(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState(false);
  
  // Saved jobs tracking
  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(new Set());
  const [savingJobId, setSavingJobId] = useState<number | null>(null);
  
  // Initial load
  useEffect(() => {
    loadJobs();
    loadSavedJobs();
  }, []);
  
  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      // Always load all jobs (no min_score filter) so we can show matched/unmatched
      const data = await scoredJobsApi.list({ 
        limit: 100,
        min_score: undefined // Load ALL jobs
      });
      setJobs(data.jobs);
    } catch (err: any) {
      console.error('Error loading jobs:', err);
      setError('Erreur lors du chargement des offres');
    } finally {
      setLoading(false);
    }
  }, []);
  
  const loadSavedJobs = useCallback(async () => {
    try {
      const data = await applicationsApi.list();
      const ids = new Set(data.applications.map(app => app.job_id));
      setSavedJobIds(ids);
    } catch (err) {
      console.error('Error loading saved jobs:', err);
    }
  }, []);
  
  const handleSaveJob = async (jobId: number) => {
    if (savedJobIds.has(jobId)) return;
    
    setSavingJobId(jobId);
    try {
      await applicationsApi.create({ job_id: jobId, status: 'SAVED' });
      setSavedJobIds(prev => new Set([...prev, jobId]));
    } catch (err: any) {
      if (err.response?.status !== 400) { // Ignore "already saved" errors
        setError('Erreur lors de la sauvegarde');
      }
    } finally {
      setSavingJobId(null);
    }
  };
  
  // Handle search completion - add new jobs from FindAll
  const handleSearchComplete = useCallback((newScoredJobs?: any[]) => {
    if (newScoredJobs && newScoredJobs.length > 0) {
      // Convert to ScoredJob format and add to state
      const formattedJobs: ScoredJob[] = newScoredJobs.map(j => ({
        job: j.job,
        score: j.score,
        breakdown: j.breakdown
      }));
      
      // Merge with existing jobs (avoid duplicates)
      const existingIds = new Set(jobs.map(j => j.job.id));
      const trulyNewJobs = formattedJobs.filter(j => !existingIds.has(j.job.id));
      
      if (trulyNewJobs.length > 0) {
        const mergedJobs = [...trulyNewJobs, ...jobs].sort((a, b) => b.score - a.score);
        setJobs(mergedJobs);
      }
    } else {
      // No jobs from search, reload from DB
      loadJobs();
    }
  }, [jobs, loadJobs]);
  
  // Filter jobs based on current settings
  const filteredJobs = jobs.filter(job => {
    // Apply location filter (from saved search click)
    if (locationFilter) {
      const jobLocation = (job.job.location || '').toLowerCase();
      const filterLower = locationFilter.toLowerCase();
      // Match if job location contains the filter city
      if (!jobLocation.includes(filterLower)) return false;
    }
    // Apply minScore filter
    if (minScore > 0 && job.score < minScore) return false;
    return true;
  });
  
  const handleGenerateCoverLetter = async (job: ScoredJob) => {
    const jobId = job.job.id;
    setSelectedJob(job);
    setGeneratingCoverLetter(true);
    setCoverLetter('');
    
    try {
      const result = await api.coverLetter.generate(jobId);
      setCoverLetter(result.cover_letter);
    } catch (err: any) {
      setCoverLetter('Erreur lors de la génération de la lettre de motivation.');
    } finally {
      setGeneratingCoverLetter(false);
    }
  };
  
  const handleBlacklistCompany = async (scoredJob: ScoredJob) => {
    const company = scoredJob.job.company;
    if (!company) return;
    
    try {
      await api.blacklist.add({ company_name: company, reason: 'Blacklisté depuis le dashboard' });
      setJobs(jobs.filter(j => j.job.company !== company));
    } catch (err) {
      setError('Erreur lors du blacklist');
    }
  };
  
const getScoreColor = (score: number) => {
    if (score >= 80) return { ring: 'stroke-green-500', text: 'text-green-600', bg: 'bg-green-50' };
    if (score >= 60) return { ring: 'stroke-amber-500', text: 'text-amber-600', bg: 'bg-amber-50' };
    if (score >= 40) return { ring: 'stroke-orange-500', text: 'text-orange-600', bg: 'bg-orange-50' };
    return { ring: 'stroke-red-400', text: 'text-red-500', bg: 'bg-red-50' };
  };
  
  const getScoreLabel = (score: number) => {
    if (score >= 80) return { label: 'Excellent', color: 'bg-green-100 text-green-700 border-green-200' };
    if (score >= 60) return { label: 'Bien', color: 'bg-amber-100 text-amber-700 border-amber-200' };
    if (score >= 40) return { label: 'Moyen', color: 'bg-orange-100 text-orange-700 border-orange-200' };
    return { label: 'Faible', color: 'bg-red-100 text-red-600 border-red-200' };
  };
  
  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Recommended Jobs</h1>
          <p className="text-neutral-500">
            {filteredJobs.length > 0 
              ? `${filteredJobs.length} position${filteredJobs.length > 1 ? 's' : ''} match your profile`
              : 'Lancez une recherche pour voir les offres'
            }
          </p>
        </div>
        
        {/* Search Panel */}
        <SearchPanel 
          onSearchComplete={handleSearchComplete}
          defaultKeywords={urlKeywords || 'Product Manager'}
          defaultLocation={urlLocation || 'Toulouse'}
        />
        
        {/* Active location filter badge */}
        {locationFilter && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200">
            <MapPin className="h-4 w-4 text-blue-600" />
            <span className="text-sm text-blue-800">
              Filtre actif: <strong>{locationFilter}</strong> ({filteredJobs.length} offre{filteredJobs.length > 1 ? 's' : ''})
            </span>
            <button
              onClick={() => setLocationFilter('')}
              className="ml-auto px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition-colors"
            >
              ✕ Voir toutes les offres
            </button>
          </div>
        )}
        
        
        {/* Filters */}
        <div className="card">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-neutral-600">Score minimum:</label>
              <select
                value={minScore}
                onChange={(e) => setMinScore(parseInt(e.target.value))}
                className="input-field w-32"
              >
                <option value={0}>Tous</option>
                <option value={40}>40+ (Moyen)</option>
                <option value={60}>60+ (Bon)</option>
                <option value={80}>80+ (Excellent)</option>
              </select>
            </div>
            
            {/* Score legend */}
            <div className="flex items-center gap-3 text-xs ml-auto">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-green-500"></span> 80+ Excellent
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-primary-500"></span> 60-79 Bon
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-amber-500"></span> 40-59 Moyen
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-neutral-400"></span> &lt;40 À revoir
              </span>
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
        ) : filteredJobs.length === 0 ? (
          <div className="card text-center py-12">
            <Sparkles className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">
              {jobs.length === 0 ? 'Aucune offre trouvée' : 'Aucune offre avec ces filtres'}
            </h3>
            <p className="text-neutral-600">
              {jobs.length === 0 
                ? 'Lance une recherche ci-dessus pour trouver des offres.'
                : minScore > 0 
                  ? `Aucune offre avec un score supérieur à ${minScore}. Essaie de baisser le filtre.`
                  : 'Essaie d\'afficher les offres non-matched.'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredJobs.map((scoredJob) => {
              const job = scoredJob.job;
              const isExpanded = expandedJob === job.id;
              const scoreColors = getScoreColor(scoredJob.score);
              const scoreLabel = getScoreLabel(scoredJob.score);
              const scorePercent = Math.min(100, scoredJob.score);
              const circumference = 2 * Math.PI * 36; // radius 36
              const strokeDashoffset = circumference - (scorePercent / 100) * circumference;
              
              return (
                <div 
                  key={job.id} 
                  className="bg-white rounded-xl border border-neutral-200 p-5 hover:shadow-lg transition-all duration-200"
                >
                  <div className="flex gap-5">
                    {/* Job info - left side */}
                    <div className="flex-1 min-w-0">
                      {/* Title */}
                      <h3 className="text-lg font-semibold text-neutral-900 mb-1">
                        {job.title}
                      </h3>
                      
                      {/* Company */}
                      <p className="text-neutral-600 mb-3">
                        {job.company || 'À déterminer'}
                      </p>
                      
                      {/* Meta info */}
                      <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-500 mb-4">
                        <span className="flex items-center gap-1.5">
                          <MapPin className="h-4 w-4" />
                          {cleanLocation(job.location)}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Briefcase className="h-4 w-4" />
                          CDI
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Clock className="h-4 w-4" />
                          {job.posted_at ? new Date(job.posted_at).toLocaleDateString('fr-FR') : 'Date inconnue'}
                        </span>
                      </div>
                      
                      {/* Salary if available */}
                      {scoredJob.breakdown.salary.salary && (
                        <p className="text-neutral-900 font-medium mb-4">
                          {scoredJob.breakdown.salary.salary}€ / an
                        </p>
                      )}
                      
                      {/* Score details inline */}
                      <div className="text-sm text-neutral-600 mb-4">
                        <p className="font-medium text-neutral-700 mb-1">Détail du score:</p>
                        <div className="flex flex-wrap gap-x-6 gap-y-1">
                          <span>Rôle: {scoredJob.breakdown.role.points}</span>
                          <span>Compétences: {scoredJob.breakdown.skills.points}</span>
                          <span>Géo: {scoredJob.breakdown.geography.points}</span>
                          <span>Attractivité: {scoredJob.breakdown.attractiveness.points}</span>
                          <span>Salaire: {scoredJob.breakdown.salary.points}</span>
                          <span className={scoredJob.breakdown.penalties.points < 0 ? 'text-red-600' : ''}>
                            Pénalités: {scoredJob.breakdown.penalties.points}
                          </span>
                        </div>
                      </div>
                      
                      {/* Action buttons */}
                      <div className="flex items-center gap-3">
                        {/* Save/Candidature button */}
                        <button
                          onClick={() => handleSaveJob(job.id)}
                          disabled={savedJobIds.has(job.id) || savingJobId === job.id}
                          className={`inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
                            savedJobIds.has(job.id)
                              ? 'bg-green-100 text-green-700 border border-green-200 cursor-default'
                              : 'bg-primary-500 text-white hover:bg-primary-600'
                          }`}
                        >
                          {savingJobId === job.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : savedJobIds.has(job.id) ? (
                            <Check className="h-4 w-4" />
                          ) : (
                            <Heart className="h-4 w-4" />
                          )}
                          {savedJobIds.has(job.id) ? 'Sauvegradé' : 'Candidater'}
                        </button>
                        
                        {job.source_url && (
                          <a
                            href={job.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 text-sm text-neutral-700 border border-neutral-300 rounded-lg hover:bg-neutral-50 transition-colors"
                          >
                            <ExternalLink className="h-4 w-4" />
                            Voir l'offre
                          </a>
                        )}
                        <button
                          onClick={() => handleGenerateCoverLetter(scoredJob)}
                          className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition-colors"
                        >
                          <span>✏️</span>
                          Générer lettre
                        </button>
                        <button
                          onClick={() => handleBlacklistCompany(scoredJob)}
                          className="p-2 text-neutral-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title="Blacklister cette entreprise"
                        >
                          <Ban className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    
                    {/* Score circle - right side */}
                    <div className="flex flex-col items-center gap-2">
                      <div className="relative w-24 h-24">
                        {/* Background circle */}
                        <svg className="w-24 h-24 transform -rotate-90">
                          <circle
                            cx="48"
                            cy="48"
                            r="36"
                            fill="none"
                            stroke="#f3f4f6"
                            strokeWidth="6"
                          />
                          {/* Progress circle */}
                          <circle
                            cx="48"
                            cy="48"
                            r="36"
                            fill="none"
                            className={scoreColors.ring}
                            strokeWidth="6"
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                          />
                        </svg>
                        {/* Score text */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className={`text-2xl font-bold ${scoreColors.text}`}>
                            {Math.round(scoredJob.score)}
                          </span>
                          <span className="text-xs text-neutral-400">/ 100</span>
                        </div>
                      </div>
                      
                      {/* Score label badge */}
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${scoreLabel.color}`}>
                        {scoreLabel.label}
                      </span>
                      
                      {/* Score adjustment if penalties */}
                      {scoredJob.breakdown.penalties.points < 0 && (
                        <div className="text-xs text-neutral-500 text-center">
                          <span className="block">Score ajusté</span>
                          <span className="text-neutral-400 line-through">
                            {Math.round(scoredJob.score - scoredJob.breakdown.penalties.points)}
                          </span>
                          <span className="mx-1">→</span>
                          <span className={scoreColors.text}>{Math.round(scoredJob.score)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Expand/collapse for full breakdown */}
                  <button
                    onClick={() => setExpandedJob(isExpanded ? null : job.id)}
                    className="mt-4 pt-4 border-t border-neutral-100 w-full flex items-center justify-center gap-1 text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp className="h-4 w-4" />
                        Masquer le détail
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        Voir le détail du score
                      </>
                    )}
                  </button>
                  
                  {/* Full breakdown panel */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-neutral-100">
                      <ScoreBreakdownPanel breakdown={scoredJob.breakdown} />
                    </div>
                  )}
                </div>
              );
            })}
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
                Pour: {selectedJob.job.title} chez {selectedJob.job.company}
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
