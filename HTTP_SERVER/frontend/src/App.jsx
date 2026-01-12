import React, { useState } from 'react';
import FileExplorer from './components/FileExplorer';
import LogModal from './components/LogModal';
import { Layout } from 'lucide-react';
import logo from './assets/logo.jpg';

function App() {
    const [selectedLog, setSelectedLog] = useState(null);

    return (
        <div className="min-h-screen bg-gray-50 text-gray-900 font-sans p-4 md:px-8 lg:px-12 flex flex-col">
            <div className="w-full flex-grow flex flex-col">
                <header className="mb-8 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-white p-1 rounded-xl shadow-md overflow-hidden border border-gray-100">
                            <img src={logo} alt="Logo" className="w-10 h-10 object-contain" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
                                Rpi logs <span className="text-blue-600">cloud storage</span>
                            </h1>
                            <p className="text-gray-500 font-medium">Secure log management and storage system</p>
                        </div>
                    </div>
                </header>

                <main className="flex-grow flex flex-col">
                    <FileExplorer onViewLog={(log) => setSelectedLog(log)} />
                </main>

                <footer className="mt-12 text-center text-gray-400 text-sm font-medium">
                    © 2026 Rpi logs cloud storage &bull; Built with ❤️ at accolade
                </footer>
            </div>

            {selectedLog && (
                <LogModal
                    log={selectedLog}
                    onClose={() => setSelectedLog(null)}
                />
            )}
        </div>
    );
}

export default App;
