import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

/**
 * Simple markdown renderer for copilot responses.
 * Handles basic markdown formatting without external dependencies.
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const renderContent = (text: string) => {
    // Split by lines to handle block-level elements
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockLines: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          elements.push(
            <pre key={i} className="bg-gray-800 text-gray-100 p-3 rounded my-2 overflow-x-auto">
              <code>{codeBlockLines.join('\n')}</code>
            </pre>
          );
          codeBlockLines = [];
          inCodeBlock = false;
        } else {
          // Start code block
          inCodeBlock = true;
        }
        continue;
      }

      if (inCodeBlock) {
        codeBlockLines.push(line);
        continue;
      }

      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={i} className="text-lg font-semibold mt-3 mb-2">
            {renderInline(line.substring(4))}
          </h3>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={i} className="text-xl font-bold mt-4 mb-2">
            {renderInline(line.substring(3))}
          </h2>
        );
      } else if (line.startsWith('# ')) {
        elements.push(
          <h1 key={i} className="text-2xl font-bold mt-4 mb-3">
            {renderInline(line.substring(2))}
          </h1>
        );
      }
      // Lists
      else if (line.startsWith('- ')) {
        elements.push(
          <li key={i} className="ml-4">
            {renderInline(line.substring(2))}
          </li>
        );
      }
      // Empty lines
      else if (line.trim() === '') {
        elements.push(<br key={i} />);
      }
      // Regular paragraphs
      else {
        elements.push(
          <p key={i} className="my-1">
            {renderInline(line)}
          </p>
        );
      }
    }

    return elements;
  };

  const renderInline = (text: string): React.ReactNode => {
    // Bold **text**
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic *text*
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Inline code `code`
    text = text.replace(/`(.+?)`/g, '<code class="bg-gray-700 px-1 rounded">$1</code>');
    
    // Links [text](url)
    text = text.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" class="text-blue-400 hover:underline">$1</a>');

    return <span dangerouslySetInnerHTML={{ __html: text }} />;
  };

  return <div className="markdown-content">{renderContent(content)}</div>;
};
