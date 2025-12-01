import { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { applicationsApi } from '../services/api';
import type { Application } from '../types';
import { 
  Loader2, MapPin, ExternalLink, Trash2, 
  Calendar, CheckCircle, Clock, XCircle,
  Phone, UserCheck, Award, FileText
} from 'lucide-react';

// Status configuration with colors and labels
const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode; bgColor: string }> = {
  SAVED: { 
    label: 'Sauvegardée', 
    color: 'text-blue-600', 
    bgColor: 'bg-blue-50 border-blue-200',
    icon: <FileText className="h-4 w-4" />
  },
  APPLIED: { 
    label: 'Candidature envoyée', 
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    icon: <CheckCircle className="h-4 w-4" />
  },
  PHONE_SCREEN: { 
    label: 'Appel téléphonique', 
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50 border-cyan-200',
    icon: <Phone className="h-4 w-4" />
  },
  INTERVIEW: { 
    label: 'Entretien', 
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 border-amber-200',
    icon: <UserCheck className="h-4 w-4" />
  },
  TECHNICAL: { 
    label: 'Test technique', 
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50 border-indigo-200',
    icon: <FileText className="h-4 w-4" />
  },
  FINAL_ROUND: { 
    label: 'Entretien final', 
    color: 'text-orange-600',
    bgColor: 'bg-orange-50 border-orange-200',
    icon: <Award className="h-4 w-4" />
  },
  OFFER: { 
    label: 'Offre reçue 🎉', 
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <Award className="h-4 w-4" />
  },
  REJECTED: { 
    label: 'Refusée', 
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
    icon: <XCircle className="h-4 w-4" />
  },
  WITHDRAWN: { 
    label: 'Retirée', 
    color: 'text-neutral-500',
    bgColor: 'bg-neutral-50 border-neutral-200',
    icon: <XCircle className="h-4 w-4" />
  },
};

const STATUS_ORDER = [
  'SAVED', 'APPLIED', 'PHONE_SCREEN', 'INTERVIEW', 
  'TECHNICAL', 'FINAL_ROUND', 'OFFER', 'REJECTED', 'WITHDRAWN'
];

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState<Record<string, number>>({});
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const [appsData, statsData] = await Promise.all([
        applicationsApi.list(),
        applicationsApi.getStats()
      ]);
      setApplications(appsData.applications);
      setStats(statsData);
    } catch (err: any) {
      console.error('Error loading applications:', err);
      setError('Erreur lors du chargement des candidatures');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    setUpdatingId(id);
    try {
      await applicationsApi.update(id, { status: newStatus as any });
      // Update local state
      setApplications(apps => 
        apps.map(app => app.id === id ? { ...app, status: newStatus as any } : app)
      );
      // Update stats
      const oldApp = applications.find(a => a.id === id);
      if (oldApp) {
        setStats(prev => ({
          ...prev,
          [oldApp.status]: Math.max(0, (prev[oldApp.status] || 0) - 1),
          [newStatus]: (prev[newStatus] || 0) + 1
        }));
      }
    } catch (err) {
      setError('Erreur lors de la mise à jour');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer cette candidature ?')) return;
    
    try {
      await applicationsApi.delete(id);
      const deletedApp = applications.find(a => a.id === id);
      setApplications(apps => apps.filter(app => app.id !== id));
      if (deletedApp) {
        setStats(prev => ({
          ...prev,
          [deletedApp.status]: Math.max(0, (prev[deletedApp.status] || 0) - 1)
        }));
      }
    } catch (err) {
      setError('Erreur lors de la suppression');
    }
  };

  // Filter applications by status
  const filteredApps = selectedStatus 
    ? applications.filter(app => app.status === selectedStatus)
    : applications;

  // Sort by created_at descending
  const sortedApps = [...filteredApps].sort((a, b) => 
    new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  );

  const totalActive = Object.entries(stats)
    .filter(([status]) => !['REJECTED', 'WITHDRAWN'].includes(status))
    .reduce((sum, [, count]) => sum + count, 0);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Mes Candidatures</h1>
          <p className="text-neutral-500">
            {totalActive} candidature{totalActive > 1 ? 's' : ''} en cours
          </p>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <button
            onClick={() => setSelectedStatus(null)}
            className={`p-4 rounded-xl border transition-all ${
              selectedStatus === null 
                ? 'bg-primary-50 border-primary-300 ring-2 ring-primary-200' 
                : 'bg-white border-neutral-200 hover:border-primary-200'
            }`}
          >
            <div className="text-2xl font-bold text-neutral-900">{applications.length}</div>
            <div className="text-sm text-neutral-600">Toutes</div>
          </button>
          
          {STATUS_ORDER.filter(status => stats[status] > 0).map(status => {
            const config = STATUS_CONFIG[status];
            return (
              <button
                key={status}
                onClick={() => setSelectedStatus(status === selectedStatus ? null : status)}
                className={`p-4 rounded-xl border transition-all ${
                  selectedStatus === status 
                    ? `${config.bgColor} ring-2 ring-opacity-50` 
                    : 'bg-white border-neutral-200 hover:border-neutral-300'
                }`}
              >
                <div className={`text-2xl font-bold ${config.color}`}>{stats[status] || 0}</div>
                <div className="text-sm text-neutral-600 truncate">{config.label}</div>
              </button>
            );
          })}
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Applications list */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : sortedApps.length === 0 ? (
          <div className="card text-center py-12">
            <FileText className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">
              {applications.length === 0 ? 'Aucune candidature' : 'Aucune candidature avec ce statut'}
            </h3>
            <p className="text-neutral-600">
              {applications.length === 0 
                ? 'Sauvegarde des offres depuis le Dashboard pour commencer à suivre tes candidatures.'
                : 'Sélectionne un autre filtre pour voir tes candidatures.'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedApps.map((app) => {
              const statusConfig = STATUS_CONFIG[app.status] || STATUS_CONFIG.SAVED;
              const job = app.job;
              
              return (
                <div 
                  key={app.id} 
                  className={`bg-white rounded-xl border p-5 hover:shadow-md transition-all ${statusConfig.bgColor}`}
                >
                  <div className="flex items-start gap-4">
                    {/* Status badge */}
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${statusConfig.bgColor} ${statusConfig.color} text-sm font-medium`}>
                      {statusConfig.icon}
                      {statusConfig.label}
                    </div>
                    
                    {/* Job info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-neutral-900 mb-1">
                        {job?.title || 'Poste non disponible'}
                      </h3>
                      <p className="text-neutral-600 mb-2">
                        {job?.company || 'Entreprise non spécifiée'}
                      </p>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-500">
                        {job?.location && (
                          <span className="flex items-center gap-1.5">
                            <MapPin className="h-4 w-4" />
                            {job.location.split(';')[0].split(',').slice(0, 2).join(', ')}
                          </span>
                        )}
                        <span className="flex items-center gap-1.5">
                          <Calendar className="h-4 w-4" />
                          Ajoutée le {app.created_at ? new Date(app.created_at).toLocaleDateString('fr-FR') : 'N/A'}
                        </span>
                        {app.applied_at && (
                          <span className="flex items-center gap-1.5">
                            <Clock className="h-4 w-4" />
                            Postulée le {new Date(app.applied_at).toLocaleDateString('fr-FR')}
                          </span>
                        )}
                      </div>
                      
                      {/* Notes */}
                      {app.notes && (
                        <p className="mt-3 text-sm text-neutral-600 bg-neutral-50 p-2 rounded">
                          {app.notes}
                        </p>
                      )}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex flex-col items-end gap-2">
                      {/* Status selector */}
                      <select
                        value={app.status}
                        onChange={(e) => handleUpdateStatus(app.id, e.target.value)}
                        disabled={updatingId === app.id}
                        className="input-field text-sm py-1.5 pr-8"
                      >
                        {STATUS_ORDER.map(status => (
                          <option key={status} value={status}>
                            {STATUS_CONFIG[status].label}
                          </option>
                        ))}
                      </select>
                      
                      {/* Action buttons */}
                      <div className="flex items-center gap-2">
                        {job?.source_url && (
                          <a
                            href={job.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 text-neutral-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            title="Voir l'offre"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <button
                          onClick={() => handleDelete(app.id)}
                          className="p-2 text-neutral-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                          title="Supprimer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
