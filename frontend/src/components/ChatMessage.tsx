import React from 'react';

interface Source {
  order_number: string;
  title: string;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, sources }) => {
  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${
          role === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 dark:bg-gray-800'
        }`}
      >
        <p className="whitespace-pre-wrap">{content}</p>
        {sources && sources.length > 0 && (
          <div className="mt-2 text-sm border-t pt-2">
            <p className="font-semibold">Sources:</p>
            <ul className="list-disc list-inside">
              {sources.map((source, index) => (
                <li key={index}>
                  Executive Order {source.order_number}: {source.title}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
