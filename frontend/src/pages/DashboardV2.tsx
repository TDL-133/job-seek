import { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { scoredJobsApi, type ScoredJob, type ScoreBreakdown } from '../services/api';
import { 
  Loader2, MapPin, Building2, Clock, ExternalLink, 
  FileText, Ban, ChevronDown, ChevronUp, Sparkles, RefreshCw,
  Eye, EyeOff
} from 'lucide-react';
import { api } from '../services/api';
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

// Seniority badge
function SeniorityBadge({ level, label }: { level: string; label: string }) {
  const colors: Record<string, string> = {
    head: 'bg-purple-100 text-purple-700 border-purple-200',
    senior: 'bg-green-100 text-green-700 border-green-200',
    mid: 'bg-blue-100 text-blue-700 border-blue-200',
    junior: 'bg-amber-100 text-amber-700 border-amber-200',
    unknown: 'bg-neutral-100 text-neutral-600 border-neutral-200',
  };
  
  const emojis: Record<string, string> = {
    head: '👑',
    senior: '⭐',
    mid: '💼',
    junior: '🌱',
    unknown: '❓',
  };
  
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${colors[level] || colors.unknown}`}>
      {emojis[level] || emojis.unknown} {label}
    </span>
  );
}

// Match threshold - jobs with score >= this are considered "matched"
const MATCH_THRESHOLD = 40;

export default function DashboardV2() {
  const [jobs, setJobs] = useState<ScoredJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [total, setTotal] = useState(0);
  
  // Filters
  const [minScore, setMinScore] = useState<number>(0);
  const [showUnmatched, setShowUnmatched] = useState(true);
  const [expandedJob, setExpandedJob] = useState<number | null>(null);
  
  // Cover letter
  const [selectedJob, setSelectedJob] = useState<ScoredJob | null>(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState(false);
  
  // Initial load
  useEffect(() => {
    loadJobs();
  }, []);
  
  // Re-load when filters change
  useEffect(() => {
    if (!loading) {
      loadJobs();
    }
  }, [minScore]);
  
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
      setTotal(data.total);
    } catch (err: any) {
      console.error('Error loading jobs:', err);
      setError('Erreur lors du chargement des offres');
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Filter jobs based on current settings
  const filteredJobs = jobs.filter(job => {
    // Apply minScore filter
    if (minScore > 0 && job.score < minScore) return false;
    // Hide unmatched if toggle is off
    if (!showUnmatched && job.score < MATCH_THRESHOLD) return false;
    return true;
  });
  
  // Count matched and unmatched
  const matchedCount = jobs.filter(j => j.score >= MATCH_THRESHOLD).length;
  const unmatchedCount = jobs.filter(j => j.score < MATCH_THRESHOLD).length;
  
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
  
  const handleBlacklistCompany = async (job: ScoredJob) => {
    const company = job.job.company;
    if (!company) return;
    
    try {
      await api.blacklist.add({ company_name: company, reason: 'Blacklisté depuis le dashboard' });
      setJobs(jobs.filter(j => j.job.company !== company));
    } catch (err) {
      setError('Erreur lors du blacklist');
    }
  };
  
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100 border-green-200';
    if (score >= 60) return 'text-primary-600 bg-primary-100 border-primary-200';
    if (score >= 40) return 'text-amber-600 bg-amber-100 border-amber-200';
    return 'text-neutral-600 bg-neutral-100 border-neutral-200';
  };
  
  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">🎯 Recherche d'emploi</h1>
            <p className="text-neutral-600">
              Trouvez les offres qui correspondent à votre profil
            </p>
          </div>
          <button
            onClick={loadJobs}
            disabled={loading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Actualiser scores
          </button>
        </div>
        
        {/* Search Panel */}
        <SearchPanel 
          onSearchComplete={loadJobs}
          defaultKeywords="Product Manager"
          defaultLocation="Paris"
        />
        
        {/* Stats */}
        {total > 0 && (
          <div className="flex flex-wrap gap-4">
            <div className="px-4 py-2 rounded-lg bg-green-50 text-green-800 text-sm">
              ✅ <span className="font-medium">{matchedCount}</span> offre{matchedCount > 1 ? 's' : ''} matched (score ≥ {MATCH_THRESHOLD})
            </div>
            <div className="px-4 py-2 rounded-lg bg-neutral-100 text-neutral-600 text-sm">
              📋 <span className="font-medium">{unmatchedCount}</span> offre{unmatchedCount > 1 ? 's' : ''} à revoir (score &lt; {MATCH_THRESHOLD})
            </div>
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
            
            {/* Show/hide unmatched toggle */}
            <button
              onClick={() => setShowUnmatched(!showUnmatched)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                showUnmatched 
                  ? 'bg-neutral-100 text-neutral-700' 
                  : 'bg-neutral-200 text-neutral-500'
              }`}
            >
              {showUnmatched ? (
                <><Eye className="h-4 w-4" /> Offres non-matched visibles</>
              ) : (
                <><EyeOff className="h-4 w-4" /> Offres non-matched masquées</>
              )}
            </button>
            
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
              const isMatched = scoredJob.score >= MATCH_THRESHOLD;
              
              return (
                <div 
                  key={job.id} 
                  className={`card hover:shadow-md transition-shadow ${
                    !isMatched ? 'opacity-75 border-l-4 border-l-neutral-300' : 'border-l-4 border-l-green-500'
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                    {/* Score + Match badge */}
                    <div className="lg:w-24 flex lg:flex-col items-center gap-2">
                      <div className={`w-16 h-16 rounded-xl flex flex-col items-center justify-center font-bold border-2 ${getScoreColor(scoredJob.score)}`}>
                        <span className="text-2xl">{Math.round(scoredJob.score)}</span>
                        <span className="text-[10px] uppercase tracking-wide opacity-70">pts</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        isMatched 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-neutral-100 text-neutral-500'
                      }`}>
                        {isMatched ? '✅ Match' : '📋 À revoir'}
                      </span>
                    </div>
                    
                    {/* Job info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <h3 className="font-semibold text-neutral-900">
                              {job.title}
                            </h3>
                            {/* Seniority badge */}
                            <SeniorityBadge 
                              level={scoredJob.breakdown.role.level}
                              label={scoredJob.breakdown.role.label}
                            />
                          </div>
                          
                          <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-600">
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
                            {job.source && (
                              <span className="flex items-center gap-1 text-neutral-400">
                                📡 {job.source}
                              </span>
                            )}
                            {job.posted_at && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                {new Date(job.posted_at).toLocaleDateString('fr-FR')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Quick score summary */}
                      <div className="flex flex-wrap gap-2 mt-3">
                        <span className="text-xs px-2 py-1 rounded bg-neutral-100 text-neutral-600">
                          {scoredJob.breakdown.geography.details}
                        </span>
                        {scoredJob.breakdown.salary.salary && (
                          <span className="text-xs px-2 py-1 rounded bg-green-50 text-green-700">
                            {scoredJob.breakdown.salary.details}
                          </span>
                        )}
                        {scoredJob.breakdown.skills.matched > 0 && (
                          <span className="text-xs px-2 py-1 rounded bg-purple-50 text-purple-700">
                            {scoredJob.breakdown.skills.matched} skills matchés
                          </span>
                        )}
                        {scoredJob.breakdown.attractiveness.level !== 'low' && (
                          <span className="text-xs px-2 py-1 rounded bg-amber-50 text-amber-700">
                            {scoredJob.breakdown.attractiveness.details}
                          </span>
                        )}
                        {scoredJob.breakdown.penalties.points < 0 && (
                          <span className="text-xs px-2 py-1 rounded bg-red-50 text-red-600">
                            {scoredJob.breakdown.penalties.points} pts
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex lg:flex-col gap-2">
                      {job.source_url && (
                        <a
                          href={job.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-primary text-sm"
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Voir
                        </a>
                      )}
                      <button
                        onClick={() => handleGenerateCoverLetter(scoredJob)}
                        className="btn-secondary text-sm"
                      >
                        <FileText className="h-4 w-4 mr-1" />
                        Lettre
                      </button>
                      <button
                        onClick={() => handleBlacklistCompany(scoredJob)}
                        className="btn-ghost text-sm text-neutral-500 hover:text-red-600"
                        title="Blacklister cette entreprise"
                      >
                        <Ban className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Expand/collapse for full breakdown */}
                  <button
                    onClick={() => setExpandedJob(isExpanded ? null : job.id)}
                    className="mt-4 pt-4 border-t border-neutral-100 w-full flex items-center justify-center gap-1 text-sm text-neutral-600 hover:text-primary-600"
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
