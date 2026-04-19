import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const mdComponents = {
  h1: ({children}) => (
    <h1 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 26, color: '#A78BFA', marginTop: 32, marginBottom: 12 }}>{children}</h1>
  ),
  h2: ({children}) => (
    <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: '#A78BFA', marginTop: 28, marginBottom: 10, borderBottom: '1px solid rgba(167,139,250,0.15)', paddingBottom: 6 }}>{children}</h2>
  ),
  h3: ({children}) => (
    <h3 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 16, color: '#c4b5fd', marginTop: 20, marginBottom: 8 }}>{children}</h3>
  ),
  p: ({children}) => (
    <p style={{ fontFamily: 'Inter', fontSize: 14, color: '#D4D4D8', lineHeight: 1.75, marginBottom: 12, fontWeight: 300 }}>{children}</p>
  ),
  strong: ({children}) => (
    <strong style={{ color: '#fff', fontWeight: 600 }}>{children}</strong>
  ),
  ul: ({children}) => <ul style={{ paddingLeft: 20, marginBottom: 12, listStyleType: 'disc' }}>{children}</ul>,
  ol: ({children}) => <ol style={{ paddingLeft: 20, marginBottom: 12 }}>{children}</ol>,
  li: ({children}) => <li style={{ fontFamily: 'Inter', fontSize: 14, color: '#D4D4D8', lineHeight: 1.75, marginBottom: 4, fontWeight: 300 }}>{children}</li>,
  blockquote: ({children}) => (
    <blockquote style={{ borderLeft: '3px solid rgba(167,139,250,0.4)', paddingLeft: 16, margin: '12px 0', color: '#A1A1AA' }}>{children}</blockquote>
  ),
  code: ({inline, children}) => inline
    ? <code style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 4, padding: '1px 5px', fontFamily: 'monospace', fontSize: 12, color: '#c4b5fd' }}>{children}</code>
    : <pre style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '12px 16px', overflowX: 'auto', marginBottom: 12 }}><code style={{ fontFamily: 'monospace', fontSize: 12, color: '#D4D4D8' }}>{children}</code></pre>,
  table: ({children}) => (
    <div style={{ overflowX: 'auto', marginBottom: 16 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'Inter', fontSize: 12 }}>{children}</table>
    </div>
  ),
  thead: ({children}) => <thead style={{ background: 'rgba(255,255,255,0.04)' }}>{children}</thead>,
  th: ({children}) => <th style={{ padding: '8px 12px', textAlign: 'left', color: '#71717A', fontWeight: 600, borderBottom: '1px solid rgba(255,255,255,0.1)', whiteSpace: 'nowrap' }}>{children}</th>,
  td: ({children}) => <td style={{ padding: '7px 12px', color: '#D4D4D8', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>{children}</td>,
  hr: () => <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)', margin: '24px 0' }} />,
  a: ({href, children}) => <a href={href} target="_blank" rel="noreferrer" style={{ color: '#c4b5fd', textDecoration: 'underline', textUnderlineOffset: '2px' }}>{children}</a>,
};

export default function StyledMarkdown({ children }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
      {children}
    </ReactMarkdown>
  );
}

export { mdComponents };
