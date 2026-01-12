import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, FileText, Loader2 } from 'lucide-react';

const LogModal = ({ log, onClose }) => {
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const scrollRef = React.useRef(null);

    const fetchContent = async (currentOffset) => {
        try {
            if (currentOffset === 0) setLoading(true);
            else setLoadingMore(true);

            const response = await axios.get(`/view/${log.id}?offset=${currentOffset}`);
            const { content: newContent, next_offset } = response.data;

            setContent(prev => currentOffset === 0 ? newContent : prev + newContent);
            setOffset(next_offset);
            setHasMore(next_offset !== null);
        } catch (error) {
            if (currentOffset === 0) setContent('Error loading log content.');
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    useEffect(() => {
        fetchContent(0);
    }, [log.id]);

    const handleScroll = (e) => {
        const { scrollTop, scrollHeight, clientHeight } = e.target;
        // Reach bottom? (50px threshold)
        if (scrollHeight - scrollTop <= clientHeight + 50) {
            if (!loadingMore && hasMore) {
                fetchContent(offset);
            }
        }
    };

    const highlightContent = (text) => {
        if (!text && !loading) return '<span class="text-gray-500 italic">No content available in this log file.</span>';
        if (!text) return '';

        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/(ERROR|ERR)/gi, '<span class="text-red-400 font-bold">$1</span>')
            .replace(/(WARNING|WARN)/gi, '<span class="text-yellow-400 font-bold">$1</span>')
            .replace(/(INFO)/gi, '<span class="text-blue-400 font-bold">$1</span>')
            .replace(/(DEBUG)/gi, '<span class="text-gray-400 font-bold">$1</span>');
    };

    return (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div
                className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <h2 className="text-xl font-bold flex items-center gap-2 text-gray-800">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <span className="truncate max-w-[300px] md:max-w-md">{log.original_filename}</span>
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-200 rounded-full transition-colors text-gray-500"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <div
                    className="p-6 overflow-auto bg-[#0d1117] text-gray-300 font-mono text-sm leading-relaxed flex-grow"
                    onScroll={handleScroll}
                    ref={scrollRef}
                >
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 gap-4 text-gray-500">
                            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                            <p className="font-medium">Initializing log viewer...</p>
                        </div>
                    ) : (
                        <>
                            <pre
                                className="whitespace-pre-wrap break-all"
                                dangerouslySetInnerHTML={{ __html: highlightContent(content) }}
                            />
                            {loadingMore && (
                                <div className="py-4 flex items-center justify-center gap-2 text-gray-500 border-t border-gray-800 mt-4">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Scanning for more lines...</span>
                                </div>
                            )}
                            {!hasMore && content && (
                                <div className="py-4 text-center text-gray-600 italic text-xs border-t border-gray-800 mt-4">
                                    End of log file.
                                </div>
                            )}
                        </>
                    )}
                </div>

                <div className="p-4 border-t border-gray-100 bg-gray-50/50 flex justify-between items-center">
                    <span className="text-xs text-gray-400 font-medium">
                        {hasMore ? 'Scroll down to load more content' : 'Full log loaded'}
                    </span>
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-all font-semibold shadow-lg shadow-gray-200"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LogModal;
