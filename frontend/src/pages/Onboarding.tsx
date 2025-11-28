import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function Onboarding() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError('');
    if (acceptedFiles.length > 0) {
      const f = acceptedFiles[0];
      // Validate file type
      if (!f.type.includes('pdf')) {
        setError('Seuls les fichiers PDF sont acceptés');
        return;
      }
      // Validate file size (5MB max)
      if (f.size > 5 * 1024 * 1024) {
        setError('Le fichier ne doit pas dépasser 5MB');
        return;
      }
      setFile(f);
    }
  }, []);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    multiple: false,
  });
  
  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setError('');
    
    try {
      await api.profile.uploadCV(file);
      setSuccess(true);
      // Wait a bit then redirect to profile validation
      setTimeout(() => {
        navigate('/profile');
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erreur lors de l'upload du CV");
    } finally {
      setUploading(false);
    }
  };
  
  const handleSkip = () => {
    navigate('/criteria');
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-primary-50 px-4 py-10">
      <div className="max-w-2xl mx-auto">
        {/* Progress indicator */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center font-semibold">1</div>
            <div className="w-16 h-1 bg-neutral-300 rounded"></div>
            <div className="w-8 h-8 rounded-full bg-neutral-300 text-neutral-600 flex items-center justify-center font-semibold">2</div>
            <div className="w-16 h-1 bg-neutral-300 rounded"></div>
            <div className="w-8 h-8 rounded-full bg-neutral-300 text-neutral-600 flex items-center justify-center font-semibold">3</div>
          </div>
        </div>
        
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-neutral-900">
            Importe ton CV
          </h1>
          <p className="mt-2 text-neutral-600">
            On va analyser ton CV pour mieux comprendre ton profil et te proposer des offres adaptées.
          </p>
        </div>
        
        <div className="card">
          {success ? (
            <div className="text-center py-8">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                CV uploadé avec succès !
              </h3>
              <p className="text-neutral-600">
                Redirection vers la validation de ton profil...
              </p>
            </div>
          ) : (
            <>
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all
                  ${isDragActive 
                    ? 'border-primary-500 bg-primary-50' 
                    : file 
                      ? 'border-green-400 bg-green-50' 
                      : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
                  }
                `}
              >
                <input {...getInputProps()} />
                
                {file ? (
                  <div className="space-y-3">
                    <FileText className="h-12 w-12 text-green-500 mx-auto" />
                    <p className="font-medium text-neutral-900">{file.name}</p>
                    <p className="text-sm text-neutral-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                    <p className="text-xs text-neutral-400">
                      Clique ou dépose un autre fichier pour remplacer
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Upload className={`h-12 w-12 mx-auto ${isDragActive ? 'text-primary-500' : 'text-neutral-400'}`} />
                    <p className="font-medium text-neutral-900">
                      {isDragActive ? 'Dépose ton CV ici' : 'Glisse-dépose ton CV ici'}
                    </p>
                    <p className="text-sm text-neutral-500">
                      ou clique pour sélectionner un fichier
                    </p>
                    <p className="text-xs text-neutral-400">
                      PDF uniquement, 5MB max
                    </p>
                  </div>
                )}
              </div>
              
              {error && (
                <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm flex items-center">
                  <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                  {error}
                </div>
              )}
              
              <div className="mt-6 flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="btn-primary flex-1 py-3"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin mr-2" />
                      Analyse en cours...
                    </>
                  ) : (
                    'Analyser mon CV'
                  )}
                </button>
                
                <button
                  onClick={handleSkip}
                  className="btn-secondary py-3"
                >
                  Passer cette étape
                </button>
              </div>
            </>
          )}
        </div>
        
        <div className="mt-8 text-center">
          <h3 className="font-medium text-neutral-900 mb-4">
            Pourquoi importer ton CV ?
          </h3>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-xl">🎯</span>
              </div>
              <p className="text-neutral-600">
                Extraction automatique de tes compétences et expériences
              </p>
            </div>
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-xl">⚡</span>
              </div>
              <p className="text-neutral-600">
                Matching intelligent avec les offres d'emploi
              </p>
            </div>
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="text-xl">📝</span>
              </div>
              <p className="text-neutral-600">
                Génération de lettres de motivation personnalisées
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
