import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Folder,
    FileText,
    ChevronRight,
    Home,
    Eye,
    Download,
    Trash2,
    Calendar,
    Search,
    ArrowLeft
} from 'lucide-react';

const FileExplorer = ({ onViewLog }) => {
    const [logs, setLogs] = useState([]);
    const [path, setPath] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLogs();
    }, []);

    const fetchLogs = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/logs');
            setLogs(response.data);
        } catch (error) {
            console.error('Error fetching logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const deleteLog = async (id, filename) => {
        if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;
        try {
            await axios.delete(`/delete/${id}`);
            fetchLogs();
        } catch (error) {
            alert('Error deleting log');
        }
    };

    const deleteFolder = async (folder) => {
        const isDateLevel = path.length === 1;
        const msg = isDateLevel
            ? `Are you sure you want to delete all logs for ${path[0]} on ${folder.name}?`
            : `Are you sure you want to delete all logs for user ${folder.name}?`;

        if (!window.confirm(msg)) return;

        try {
            const params = isDateLevel
                ? { user: path[0], date: folder.name }
                : { user: folder.name };
            await axios.delete('/delete_folder/', { params });
            fetchLogs();
        } catch (error) {
            alert('Error deleting folder');
        }
    };

    const downloadFolderZip = (folder) => {
        const isDateLevel = path.length === 1;
        const params = isDateLevel
            ? `user=${path[0]}&date=${folder.name}`
            : `user=${folder.name}`;
        window.location.href = `/download_folder/?${params}`;
    };

    const formatFileSize = (bytes) => {
        if (!bytes || bytes === 0) return '0 KB';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    const getItemsAtCurrentPath = () => {
        const items = new Map();
        logs.forEach(log => {
            const cleanPath = log.filename.replace(/\\/g, '/').split('/');
            const logPath = [log.user, cleanPath[1]];

            const isUnderPath = path.every((segment, index) => logPath[index] === segment);

            if (isUnderPath) {
                if (path.length < 2) {
                    const nextSegment = logPath[path.length];
                    if (!items.has(nextSegment)) {
                        items.set(nextSegment, {
                            type: 'folder',
                            name: nextSegment,
                            itemCount: 0,
                            modified: log.timestamp,
                            user: log.user
                        });
                    }
                    items.get(nextSegment).itemCount++;
                } else {
                    items.set(log.id, { type: 'file', data: log });
                }
            }
        });
        return Array.from(items.values());
    };

    const navigateTo = (segment) => setPath([...path, segment]);
    const navigateBack = () => setPath(path.slice(0, -1));
    const goToBreadcrumb = (index) => setPath(path.slice(0, index + 1));

    const currentItems = getItemsAtCurrentPath();

    if (loading) return <div className="p-8 text-center text-gray-500 font-medium font-sans">Loading explorer...</div>;

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col flex-grow">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
                <div className="flex items-center gap-4">
                    {path.length > 0 && (
                        <button onClick={navigateBack} className="p-2 hover:bg-gray-200 rounded-full transition-colors">
                            <ArrowLeft className="w-5 h-5 text-gray-600" />
                        </button>
                    )}
                    <nav className="flex items-center text-sm font-medium text-gray-600">
                        <button onClick={() => setPath([])} className="hover:text-blue-600 flex items-center gap-1">
                            <Home className="w-4 h-4" />
                            <span>Drive</span>
                        </button>
                        {path.map((segment, index) => (
                            <React.Fragment key={index}>
                                <ChevronRight className="w-4 h-4 mx-1 text-gray-400" />
                                <button
                                    onClick={() => goToBreadcrumb(index)}
                                    className={`hover:text-blue-600 ${index === path.length - 1 ? 'text-gray-900 font-bold' : ''}`}
                                >
                                    {segment}
                                </button>
                            </React.Fragment>
                        ))}
                    </nav>
                </div>
            </div>

            <div className="flex-grow overflow-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="text-[13px] font-semibold text-gray-600 bg-white border-b border-gray-100">
                            <th className="px-6 py-3 font-medium">Name</th>
                            <th className="px-6 py-3 font-medium">Modified</th>
                            <th className="px-6 py-3 font-medium">Modified By</th>
                            <th className="px-6 py-3 font-medium">File size</th>
                            <th className="px-6 py-3 font-medium">Sharing</th>
                            <th className="px-6 py-3 font-medium text-center">Activity</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {currentItems.length === 0 ? (
                            <tr><td colSpan="6" className="px-6 py-12 text-center text-gray-400 italic">No items found.</td></tr>
                        ) : (
                            currentItems.map((item) => (
                                <tr
                                    key={item.type === 'folder' ? item.name : item.data.id}
                                    className="hover:bg-gray-50 transition-colors group cursor-pointer"
                                    onClick={() => item.type === 'folder' ? navigateTo(item.name) : null}
                                >
                                    <td className="px-6 py-3">
                                        <div className="flex items-center gap-3">
                                            {item.type === 'folder' ? (
                                                path.length === 0 ? <Folder className="w-5 h-5 text-amber-500 fill-amber-500/10" /> : <Calendar className="w-5 h-5 text-amber-500 fill-amber-500/10" />
                                            ) : (
                                                <div className="text-blue-600"><FileText className="w-5 h-5" /></div>
                                            )}
                                            <span className="text-[14px] font-medium text-gray-700">
                                                {item.type === 'folder' ? item.name : item.data.original_filename}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-3">
                                        <span className="text-[13px] text-gray-500">
                                            {item.type === 'folder' ? new Date(item.modified).toLocaleDateString() : new Date(item.data.timestamp).toLocaleDateString()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-3">
                                        <span className="text-[13px] text-gray-500">
                                            {item.type === 'folder' ? item.user : item.data.user}
                                        </span>
                                    </td>
                                    <td className="px-6 py-3">
                                        <span className="text-[13px] text-gray-500">
                                            {item.type === 'folder' ? '--' : formatFileSize(item.data.size)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-3">
                                        <span className="text-[13px] text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">Private</span>
                                    </td>
                                    <td className="px-6 py-3">
                                        {item.type === 'file' ? (
                                            <div className="flex items-center justify-center gap-2">
                                                <button onClick={(e) => { e.stopPropagation(); onViewLog(item.data); }} title="View" className="p-1.5 hover:bg-blue-50 text-blue-600 rounded-lg transition-colors"><Eye className="w-4 h-4" /></button>
                                                <a href={`/download/${item.data.id}`} onClick={(e) => e.stopPropagation()} title="Download" className="p-1.5 hover:bg-green-50 text-green-600 rounded-lg transition-colors"><Download className="w-4 h-4" /></a>
                                                <button onClick={(e) => { e.stopPropagation(); deleteLog(item.data.id, item.data.original_filename); }} title="Delete" className="p-1.5 hover:bg-red-50 text-red-600 rounded-lg transition-colors"><Trash2 className="w-4 h-4" /></button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center justify-center gap-2">
                                                <button onClick={(e) => { e.stopPropagation(); downloadFolderZip(item); }} title="Download Zip" className="p-1.5 hover:bg-green-50 text-green-600 rounded-lg transition-colors"><Download className="w-4 h-4" /></button>
                                                <button onClick={(e) => { e.stopPropagation(); deleteFolder(item); }} title="Delete Folder" className="p-1.5 hover:bg-red-50 text-red-600 rounded-lg transition-colors"><Trash2 className="w-4 h-4" /></button>
                                                <span className="text-[12px] text-gray-400 ml-1">{item.itemCount} files</span>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default FileExplorer;
