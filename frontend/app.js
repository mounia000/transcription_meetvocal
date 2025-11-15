const { useState, useEffect } = React;

const API_BASE = 'http://localhost:8000';

// Composant principal
const MeetVocalApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [users, setUsers] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);

  const [newUser, setNewUser] = useState({ name: '', email: '' });
  const [newMeeting, setNewMeeting] = useState({ 
    title: '', 
    date: new Date().toISOString().split('T')[0], 
    duration: 0 
  });

  useEffect(() => {
    loadUsers();
    loadMeetings();
  }, []);

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 5000);
  };

  const loadUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/users/`);
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      console.error(err);
      showMessage('error', 'Erreur lors du chargement des utilisateurs');
    }
  };

  const loadMeetings = async () => {
    try {
      const res = await fetch(`${API_BASE}/meetings/`);
      const data = await res.json();
      setMeetings(data);
    } catch (err) {
      console.error(err);
      showMessage('error', 'Erreur lors du chargement des réunions');
    }
  };

  const createUser = async () => {
    if (!newUser.name || !newUser.email) {
      showMessage('error', 'Veuillez remplir tous les champs');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/users/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser)
      });
      if (res.ok) {
        showMessage('success', 'Utilisateur créé avec succès');
        setNewUser({ name: '', email: '' });
        loadUsers();
      }
    } catch (err) {
      console.error(err);
      showMessage('error', 'Erreur lors de la création');
    }
  };

  const createMeeting = async () => {
    if (!newMeeting.title || !newMeeting.date) {
      showMessage('error', 'Veuillez remplir tous les champs');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/meetings/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMeeting)
      });
      if (res.ok) {
        showMessage('success', 'Réunion créée avec succès');
        setNewMeeting({ title: '', date: new Date().toISOString().split('T')[0], duration: 0 });
        loadMeetings();
      }
    } catch (err) {
      console.error(err);
      showMessage('error', 'Erreur lors de la création');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-m4a', 'audio/ogg', 'audio/flac'];
      const fileExt = file.name.split('.').pop().toLowerCase();
      const allowedExts = ['mp3', 'wav', 'm4a', 'ogg', 'flac'];
      
      if (!allowedExts.includes(fileExt)) {
        showMessage('error', 'Format non supporté. Utilisez: MP3, WAV, M4A, OGG, FLAC');
        e.target.value = '';
        return;
      }
      
      setSelectedFile(file);
      showMessage('success', `Fichier sélectionné: ${file.name}`);
    }
  };

  const runPipelineWithUpload = async () => {
    if (!selectedFile) {
      showMessage('error', 'Veuillez sélectionner un fichier audio');
      return;
    }

    setLoading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          setUploadProgress(Math.round(percentComplete));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          showMessage('success', `Pipeline lancé avec succès pour ${response.filename}`);
          setSelectedFile(null);
          setUploadProgress(0);
          document.getElementById('fileInput').value = '';
        } else {
          showMessage('error', 'Erreur lors du lancement du pipeline');
        }
        setLoading(false);
      });

      xhr.addEventListener('error', () => {
        showMessage('error', 'Erreur lors de l\'upload du fichier');
        setLoading(false);
      });

      xhr.open('POST', `${API_BASE}/pipeline-upload/`);
      xhr.send(formData);

    } catch (err) {
      console.error(err);
      showMessage('error', 'Erreur lors du traitement');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-indigo-600 p-2 rounded-lg">
                <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MeetVocal</h1>
                <p className="text-sm text-gray-500">Transcription & Analyse de Réunions</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Système opérationnel</span>
            </div>
          </div>
        </div>
      </header>

      {/* Message notification */}
      {message.text && (
        <div className={`max-w-7xl mx-auto px-4 py-3 mt-4 border rounded-lg ${
          message.type === 'success' 
            ? 'bg-green-100 border-green-400 text-green-700' 
            : 'bg-red-100 border-red-400 text-red-700'
        }`}>
          <span>{message.text}</span>
        </div>
      )}

      {/* Navigation */}
      <nav className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex space-x-2 bg-white p-1 rounded-lg shadow">
          {['dashboard', 'pipeline', 'users', 'meetings'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-4 py-3 rounded-md font-medium transition-all ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab === 'dashboard' && '📊 Tableau de bord'}
              {tab === 'pipeline' && '🎤 Transcription'}
              {tab === 'users' && '👥 Utilisateurs'}
              {tab === 'meetings' && '📅 Réunions'}
            </button>
          ))}
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        
        {/* Dashboard */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-indigo-600">
                <p className="text-sm text-gray-600">Total Réunions</p>
                <p className="text-3xl font-bold text-gray-900">{meetings.length}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-600">
                <p className="text-sm text-gray-600">Utilisateurs</p>
                <p className="text-3xl font-bold text-gray-900">{users.length}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-purple-600">
                <p className="text-sm text-gray-600">Statut</p>
                <p className="text-xl font-bold text-green-600">Opérationnel</p>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Réunions récentes</h2>
              {meetings.length === 0 ? (
                <p className="text-gray-500 italic">Aucune réunion pour le moment</p>
              ) : (
                <div className="space-y-3">
                  {meetings.slice(0, 5).map(meeting => (
                    <div key={meeting.id} className="p-4 bg-gray-50 rounded-lg">
                      <p className="font-semibold text-gray-900">{meeting.title}</p>
                      <p className="text-sm text-gray-500">{meeting.date} • {meeting.duration} min</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Pipeline avec Upload */}
        {activeTab === 'pipeline' && (
          <div className="bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Pipeline de Transcription</h2>
            <div className="space-y-6">
              
              {/* Zone d'upload */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-500 transition-colors">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <label className="cursor-pointer">
                  <span className="text-indigo-600 hover:text-indigo-700 font-semibold">
                    Cliquez pour sélectionner un fichier audio
                  </span>
                  <input
                    id="fileInput"
                    type="file"
                    accept=".mp3,.wav,.m4a,.ogg,.flac,audio/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
                <p className="text-sm text-gray-500 mt-2">MP3, WAV, M4A, OGG, FLAC (Max 500MB)</p>
                
                {selectedFile && (
                  <div className="mt-4 p-4 bg-indigo-50 rounded-lg">
                    <p className="text-sm font-semibold text-indigo-900">✓ Fichier sélectionné:</p>
                    <p className="text-sm text-indigo-700">{selectedFile.name}</p>
                    <p className="text-xs text-indigo-600 mt-1">
                      Taille: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                )}
              </div>

              {/* Barre de progression */}
              {loading && uploadProgress > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Upload en cours...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Le pipeline effectuera :</h3>
                <ul className="space-y-2 text-sm text-blue-800">
                  <li>• Upload du fichier audio sur le serveur</li>
                  <li>• Transcription avec diarisation (identification des locuteurs)</li>
                  <li>• Extraction et nettoyage du texte</li>
                  <li>• Génération de résumés (général et par locuteur)</li>
                  <li>• Création de PDF et Word</li>
                </ul>
              </div>

              <button
                onClick={runPipelineWithUpload}
                disabled={loading || !selectedFile}
                className={`w-full px-6 py-3 rounded-lg text-white font-semibold transition-all ${
                  loading || !selectedFile
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700 shadow-md hover:shadow-lg'
                }`}
              >
                {loading ? '⏳ Traitement en cours...' : '▶️ Lancer le Pipeline'}
              </button>
            </div>
          </div>
        )}

        {/* Users */}
        {activeTab === 'users' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Nouvel Utilisateur</h2>
              <div className="space-y-4">
                <input
                  type="text"
                  value={newUser.name}
                  onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                  placeholder="Nom complet"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  placeholder="email@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={createUser}
                  className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 font-semibold"
                >
                  Créer l'Utilisateur
                </button>
              </div>
            </div>

            <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Liste des Utilisateurs ({users.length})
              </h2>
              {users.length === 0 ? (
                <p className="text-center text-gray-500 italic py-8">Aucun utilisateur enregistré</p>
              ) : (
                <div className="space-y-3">
                  {users.map(user => (
                    <div key={user.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                      <p className="font-semibold text-gray-900">{user.name}</p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Meetings */}
        {activeTab === 'meetings' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Nouvelle Réunion</h2>
              <div className="space-y-4">
                <input
                  type="text"
                  value={newMeeting.title}
                  onChange={(e) => setNewMeeting({...newMeeting, title: e.target.value})}
                  placeholder="Titre de la réunion"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="date"
                  value={newMeeting.date}
                  onChange={(e) => setNewMeeting({...newMeeting, date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <input
                  type="number"
                  value={newMeeting.duration}
                  onChange={(e) => setNewMeeting({...newMeeting, duration: parseInt(e.target.value) || 0})}
                  placeholder="Durée (minutes)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={createMeeting}
                  className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 font-semibold"
                >
                  Créer la Réunion
                </button>
              </div>
            </div>

            <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Liste des Réunions ({meetings.length})
              </h2>
              {meetings.length === 0 ? (
                <p className="text-center text-gray-500 italic py-8">Aucune réunion enregistrée</p>
              ) : (
                <div className="space-y-3">
                  {meetings.map(meeting => (
                    <div key={meeting.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100">
                      <p className="font-semibold text-gray-900">{meeting.title}</p>
                      <p className="text-sm text-gray-500">{meeting.date} • {meeting.duration} min</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

// Rendu de l'application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(MeetVocalApp));