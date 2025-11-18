import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { filesAPI } from '../services/api';
import { 
  Upload, 
  LogOut, 
  FileAudio, 
  Clock, 
  Users, 
  Download,
  Eye,
  Loader,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await filesAPI.list();
      setFiles(response.data);
    } catch (error) {
      console.error('Erreur chargement fichiers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validation
    const validExtensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(extension)) {
      setUploadError(`Format non supporté. Utilisez: ${validExtensions.join(', ')}`);
      return;
    }

    setUploading(true);
    setUploadError('');
    setUploadSuccess('');
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);

    try {
      await filesAPI.upload(formData, (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(progress);
      });

      setUploadSuccess('✅ Transcription lancée avec succès ! Le traitement peut prendre 5-15 minutes.');
      setUploadProgress(100);
      
      // Recharger la liste après 2 secondes
      setTimeout(() => {
        loadFiles();
        setUploadSuccess('');
        setUploadProgress(0);
      }, 2000);
    } catch (error) {
      setUploadError(error.response?.data?.detail || 'Erreur lors de l\'upload');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleDownloadPDF = async (audioId, title) => {
    try {
      const response = await filesAPI.downloadPDF(audioId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${title}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert('Erreur lors du téléchargement du PDF');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      completed: { 
        icon: CheckCircle, 
        text: 'Terminé', 
        className: 'bg-green-100 text-green-800 border border-green-200' 
      },
      processing: { 
        icon: Loader, 
        text: 'En cours', 
        className: 'bg-blue-100 text-blue-800 border border-blue-200' 
      },
      failed: { 
        icon: XCircle, 
        text: 'Échoué', 
        className: 'bg-red-100 text-red-800 border border-red-200' 
      },
    };

    const config = statusConfig[status] || statusConfig.processing;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${config.className}`}>
        <Icon className="w-3.5 h-3.5" />
        {config.text}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <FileAudio className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Transcription Audio</h1>
                <p className="text-sm text-gray-600">Bienvenue, {user?.name}</p>
              </div>
            </div>
            
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
              Déconnexion
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Zone d'upload */}
        <div className="card mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Nouvelle transcription
          </h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".mp3,.wav,.m4a,.ogg,.flac"
              onChange={handleFileUpload}
              disabled={uploading}
            />
            
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="w-12 h-12 text-gray-400 mb-3" />
              <span className="text-base font-medium text-gray-900 mb-1">
                Cliquez pour uploader un fichier audio
              </span>
              <span className="text-sm text-gray-500">
                MP3, WAV, M4A, OGG, FLAC (max. 500MB)
              </span>
            </label>
          </div>

          {/* Barre de progression */}
          {uploading && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Upload en cours...</span>
                <span className="text-sm font-medium text-gray-700">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Messages */}
          {uploadError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{uploadError}</p>
            </div>
          )}

          {uploadSuccess && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3 flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-800">{uploadSuccess}</p>
            </div>
          )}
        </div>

        {/* Liste des fichiers */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Mes transcriptions
          </h2>

          {loading ? (
            <div className="text-center py-12">
              <Loader className="w-8 h-8 animate-spin text-primary-600 mx-auto" />
              <p className="mt-2 text-gray-600">Chargement...</p>
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-12">
              <FileAudio className="w-16 h-16 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600">Aucune transcription pour le moment</p>
              <p className="text-sm text-gray-500 mt-1">Uploadez votre premier fichier audio !</p>
            </div>
          ) : (
            <div className="space-y-4">
              {files.map((file) => (
                <div 
                  key={file.id_audio} 
                  className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition bg-white"
                >
                  {/* TITRE + BADGE + BOUTONS sur une ligne */}
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-gray-900 text-lg">
                        {file.title || 'Sans titre'}
                      </h3>
                      {getStatusBadge(file.status)}
                    </div>
                    
                    {/* BOUTONS À DROITE DU TITRE */}
                    {file.status === 'completed' && (
                      <div className="flex gap-2 flex-shrink-0">
                        <button
                          onClick={() => navigate(`/transcription/${file.id_audio}`)}
                          className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium shadow-sm"
                        >
                          <Eye className="w-4 h-4" />
                          Voir
                        </button>
                        <button
                          onClick={() => handleDownloadPDF(file.id_audio, file.title)}
                          className="flex items-center gap-1.5 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition text-sm font-medium shadow-sm"
                        >
                          <Download className="w-4 h-4" />
                          PDF
                        </button>
                      </div>
                    )}

                    {file.status === 'processing' && (
                      <div className="flex items-center gap-2 text-blue-600 flex-shrink-0">
                        <Loader className="w-4 h-4 animate-spin" />
                        <span className="text-sm font-medium">En cours...</span>
                      </div>
                    )}

                    {file.status === 'failed' && (
                      <div className="flex items-center gap-2 text-red-600 flex-shrink-0">
                        <XCircle className="w-4 h-4" />
                        <span className="text-sm font-medium">Échec</span>
                      </div>
                    )}
                  </div>
                  
                  {/* INFOS SUR UNE DEUXIÈME LIGNE - SÉPARÉES */}
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-50 rounded-lg text-xs text-gray-700">
                      <Clock className="w-4 h-4 text-gray-500" />
                      {formatDate(file.date_upload)}
                    </span>
                    
                    {file.duration && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 rounded-lg text-sm text-gray-700">
                        <FileAudio className="w-4 h-4 text-gray-500" />
                        {formatDuration(file.duration)}
                      </span>
                    )}
                    
                    {file.num_speakers > 0 && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 rounded-lg text-sm text-gray-700">
                        <Users className="w-4 h-4 text-gray-500" />
                        {file.num_speakers} participant{file.num_speakers > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}