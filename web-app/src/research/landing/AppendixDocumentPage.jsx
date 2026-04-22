import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

const DOC_FILES = {
  'interview-base-overview': '/appendix/interviews/A1_interview_base_overview.md',
  'interview-protocol-and-analytical-focus': '/appendix/interviews/A2_interview_protocol_and_analytical_focus.md',
  'selected-interview-excerpts': '/appendix/interviews/A3_selected_interview_excerpts.md',
};

function flushParagraph(paragraphLines, blocks) {
  if (!paragraphLines.length) return;
  blocks.push({ type: 'paragraph', text: paragraphLines.join(' ') });
  paragraphLines.length = 0;
}

function flushList(listItems, blocks) {
  if (!listItems.length) return;
  blocks.push({ type: 'list', items: [...listItems] });
  listItems.length = 0;
}

function flushTable(tableLines, blocks) {
  if (tableLines.length < 2) {
    tableLines.length = 0;
    return;
  }
  const rows = tableLines
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) =>
      line
        .split('|')
        .map((cell) => cell.trim())
        .filter((_, index, arr) => !(index === 0 && arr[0] === '') && !(index === arr.length - 1 && arr[arr.length - 1] === ''))
    );

  if (rows.length >= 2) {
    blocks.push({
      type: 'table',
      headers: rows[0],
      rows: rows.slice(2),
    });
  }
  tableLines.length = 0;
}

function parseMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  const paragraphLines = [];
  const listItems = [];
  const tableLines = [];

  const flushAll = () => {
    flushParagraph(paragraphLines, blocks);
    flushList(listItems, blocks);
    flushTable(tableLines, blocks);
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (!trimmed) {
      flushAll();
      continue;
    }

    if (trimmed.startsWith('|')) {
      flushParagraph(paragraphLines, blocks);
      flushList(listItems, blocks);
      tableLines.push(trimmed);
      continue;
    }

    if (trimmed.startsWith('# ')) {
      flushAll();
      blocks.push({ type: 'h1', text: trimmed.slice(2) });
      continue;
    }

    if (trimmed.startsWith('## ')) {
      flushAll();
      blocks.push({ type: 'h2', text: trimmed.slice(3) });
      continue;
    }

    if (trimmed.startsWith('### ')) {
      flushAll();
      blocks.push({ type: 'h3', text: trimmed.slice(4) });
      continue;
    }

    if (trimmed.startsWith('- ')) {
      flushParagraph(paragraphLines, blocks);
      flushTable(tableLines, blocks);
      listItems.push(trimmed.slice(2));
      continue;
    }

    if (trimmed.startsWith('> ')) {
      flushAll();
      blocks.push({ type: 'quote', text: trimmed.slice(2) });
      continue;
    }

    paragraphLines.push(trimmed);
  }

  flushAll();
  return blocks;
}

function renderInline(text) {
  const parts = text.split(/(“[^”]+”)/g);
  return parts.map((part, index) => {
    if (part.startsWith('“') && part.endsWith('”')) {
      return (
        <span key={index} style={{ color: '#f5f3ff' }}>
          {part}
        </span>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

export default function AppendixDocumentPage() {
  const { docId } = useParams();
  const docPath = DOC_FILES[docId];
  const [markdown, setMarkdown] = useState('');
  const [status, setStatus] = useState(docPath ? 'loading' : 'missing');

  useEffect(() => {
    if (!docPath) {
      setStatus('missing');
      return;
    }

    let active = true;
    setStatus('loading');

    fetch(docPath)
      .then((response) => {
        if (!response.ok) throw new Error('Failed to load appendix document');
        return response.text();
      })
      .then((text) => {
        if (!active) return;
        setMarkdown(text);
        setStatus('ready');
      })
      .catch(() => {
        if (!active) return;
        setStatus('error');
      });

    return () => {
      active = false;
    };
  }, [docPath]);

  const blocks = useMemo(() => parseMarkdown(markdown), [markdown]);
  const titleBlock = blocks.find((block) => block.type === 'h1');
  const introParagraph = blocks.find((block) => block.type === 'paragraph');

  if (status === 'missing') {
    return (
      <div style={{ minHeight: '100vh', background: '#09090b', color: '#fff', padding: '4rem 2rem' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '2.3rem', marginBottom: '1rem' }}>Appendix Document Not Found</h1>
          <Link to="/#scene-appendix" style={{ color: '#c4b5fd' }}>
            Back to Appendix
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#09090b', color: '#fff', padding: '4rem 2rem 5rem' }}>
      <div style={{ maxWidth: '980px', margin: '0 auto' }}>
        <Link
          to="/#scene-appendix"
          style={{
            display: 'inline-flex',
            marginBottom: '2rem',
            color: '#c4b5fd',
            textDecoration: 'underline',
            textUnderlineOffset: '3px',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.82rem',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          Back to Appendix
        </Link>

        <article
          style={{
            borderRadius: '28px',
            border: '1px solid rgba(255,255,255,0.08)',
            background: 'linear-gradient(180deg, rgba(16,12,26,0.96), rgba(10,9,16,0.99))',
            boxShadow: '0 30px 80px rgba(0,0,0,0.45)',
            padding: '3rem 3.2rem',
          }}
        >
          {status === 'loading' && (
            <p style={{ margin: 0, color: '#cbd5e1', fontFamily: 'var(--font-sans)', fontSize: '1rem' }}>Loading appendix document…</p>
          )}

          {status === 'error' && (
            <p style={{ margin: 0, color: '#fda4af', fontFamily: 'var(--font-sans)', fontSize: '1rem' }}>
              This appendix document could not be loaded.
            </p>
          )}

          {status === 'ready' && (
            <>
              {titleBlock && (
                <>
                  <div
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.82rem',
                      letterSpacing: '0.16em',
                      textTransform: 'uppercase',
                      color: '#a78bfa',
                      marginBottom: '1rem',
                    }}
                  >
                    {titleBlock.text.split('. ')[0]}
                  </div>
                  <h1
                    style={{
                      fontFamily: 'var(--font-serif)',
                      fontSize: 'clamp(2rem, 3vw, 2.8rem)',
                      lineHeight: 1.1,
                      color: '#f8fafc',
                      marginBottom: introParagraph ? '1.4rem' : '2rem',
                    }}
                  >
                    {titleBlock.text.replace(/^Appendix\s+A\d+\.\s*/, '')}
                  </h1>
                </>
              )}

              {blocks.map((block, index) => {
                if (block.type === 'h1') return null;

                if (block.type === 'h2') {
                  return (
                    <h2
                      key={`${block.type}-${index}`}
                      style={{
                        fontFamily: 'var(--font-serif)',
                        fontSize: '1.7rem',
                        lineHeight: 1.2,
                        color: '#f5f3ff',
                        margin: index === 1 ? '0 0 1rem' : '2.5rem 0 1rem',
                      }}
                    >
                      {block.text}
                    </h2>
                  );
                }

                if (block.type === 'h3') {
                  return (
                    <h3
                      key={`${block.type}-${index}`}
                      style={{
                        fontFamily: 'var(--font-sans)',
                        fontSize: '1.02rem',
                        fontWeight: 600,
                        lineHeight: 1.5,
                        color: '#c4b5fd',
                        margin: '1.6rem 0 0.7rem',
                      }}
                    >
                      {block.text}
                    </h3>
                  );
                }

                if (block.type === 'paragraph') {
                  return (
                    <p
                      key={`${block.type}-${index}`}
                      style={{
                        fontFamily: 'var(--font-sans)',
                        fontSize: '1.02rem',
                        lineHeight: 1.85,
                        color: '#cbd5e1',
                        maxWidth: '74ch',
                        margin: index === 1 ? '0 0 1.6rem' : '0 0 1.2rem',
                      }}
                    >
                      {renderInline(block.text)}
                    </p>
                  );
                }

                if (block.type === 'list') {
                  return (
                    <ul
                      key={`${block.type}-${index}`}
                      style={{
                        margin: '0 0 1.5rem 0',
                        paddingLeft: '1.45rem',
                        listStyleType: 'disc',
                        listStylePosition: 'outside',
                        display: 'grid',
                        gap: '0.55rem',
                        color: '#d4d4d8',
                        fontFamily: 'var(--font-sans)',
                        fontSize: '1rem',
                        lineHeight: 1.8,
                      }}
                    >
                      {block.items.map((item) => (
                        <li
                          key={item}
                          style={{
                            display: 'list-item',
                            paddingLeft: '0.15rem',
                          }}
                        >
                          {renderInline(item)}
                        </li>
                      ))}
                    </ul>
                  );
                }

                if (block.type === 'quote') {
                  return (
                    <blockquote
                      key={`${block.type}-${index}`}
                      style={{
                        margin: '0 0 1rem',
                        padding: '1rem 1.15rem',
                        borderLeft: '3px solid rgba(167, 139, 250, 0.5)',
                        background: 'rgba(255,255,255,0.025)',
                        borderRadius: '0 16px 16px 0',
                        fontFamily: 'var(--font-serif)',
                        fontSize: '1.02rem',
                        lineHeight: 1.7,
                        color: '#f5f3ff',
                      }}
                    >
                      “{block.text}”
                    </blockquote>
                  );
                }

                if (block.type === 'table') {
                  return (
                    <div
                      key={`${block.type}-${index}`}
                      style={{
                        overflowX: 'auto',
                        margin: '0 0 1.8rem',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '18px',
                        background: 'rgba(255,255,255,0.02)',
                      }}
                    >
                      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '680px' }}>
                        <thead>
                          <tr>
                            {block.headers.map((header) => (
                              <th
                                key={header}
                                style={{
                                  textAlign: 'left',
                                  padding: '0.95rem 1.05rem',
                                  fontFamily: 'var(--font-sans)',
                                  fontSize: '0.85rem',
                                  letterSpacing: '0.08em',
                                  textTransform: 'uppercase',
                                  color: '#c4b5fd',
                                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                                }}
                              >
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {block.rows.map((row, rowIndex) => (
                            <tr key={`${row.join('-')}-${rowIndex}`}>
                              {row.map((cell, cellIndex) => (
                                <td
                                  key={`${cell}-${cellIndex}`}
                                  style={{
                                    padding: '0.95rem 1.05rem',
                                    fontFamily: 'var(--font-sans)',
                                    fontSize: '0.98rem',
                                    lineHeight: 1.65,
                                    color: '#e5e7eb',
                                    borderTop: rowIndex === 0 ? 'none' : '1px solid rgba(255,255,255,0.05)',
                                  }}
                                >
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  );
                }

                return null;
              })}
            </>
          )}
        </article>
      </div>
    </div>
  );
}
