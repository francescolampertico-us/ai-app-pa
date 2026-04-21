import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowUpRight, BookOpen, X } from 'lucide-react';
import { REFERENCES } from './references';

export default function CitationButton({ refs = [] }) {
  const [open, setOpen] = useState(false);
  const [popupStyle, setPopupStyle] = useState(null);
  const rootRef = useRef(null);
  const popupRef = useRef(null);

  const entries = refs
    .map((ref) => ({ key: ref, ...(REFERENCES[ref] || { label: ref, apa: ref, url: '' }) }))
    .filter((entry) => !/^Primary Qualitative Data/i.test(entry.apa))
    .filter((entry, index, array) => array.findIndex((candidate) => candidate.key === entry.key) === index);

  useEffect(() => {
    if (!open || !rootRef.current || typeof window === 'undefined') return;

    const rect = rootRef.current.getBoundingClientRect();
    const viewportPadding = 16;
    const popupWidth = Math.min(380, window.innerWidth - viewportPadding * 2);
    const preferredLeft = rect.right + 16;
    const fallbackLeft = rect.left - popupWidth - 16;
    const left =
      preferredLeft + popupWidth <= window.innerWidth - viewportPadding
        ? preferredLeft
        : Math.max(viewportPadding, fallbackLeft);
    const estimatedHeight = Math.min(180 + entries.length * 108, 420);
    const top = Math.max(
      viewportPadding,
      Math.min(rect.top - 12, window.innerHeight - estimatedHeight - viewportPadding),
    );
    const maxHeight = Math.min(estimatedHeight, window.innerHeight - top - viewportPadding);

    setPopupStyle({
      top,
      left,
      width: popupWidth,
      maxHeight,
      originX: preferredLeft + popupWidth <= window.innerWidth - 16 ? '0%' : '100%',
    });
  }, [entries.length, open]);

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event) => {
      if (!rootRef.current?.contains(event.target) && !popupRef.current?.contains(event.target)) {
        setOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [open]);

  if (!entries.length) return null;

  const toggle = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setOpen((value) => !value);
  };

  return (
    <span
      ref={rootRef}
      style={{
        position: 'relative',
        display: 'inline-flex',
        marginLeft: 8,
        verticalAlign: 'middle',
        zIndex: open ? 2100 : 20,
      }}
    >
      <button
        type="button"
        aria-label="Open citations"
        aria-expanded={open}
        onClick={toggle}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') toggle(event);
        }}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 28,
          height: 28,
          borderRadius: 999,
          border: '1px solid rgba(167, 139, 250, 0.55)',
          background: open
            ? 'linear-gradient(180deg, rgba(167, 139, 250, 0.32), rgba(124, 58, 237, 0.18))'
            : 'linear-gradient(180deg, rgba(167, 139, 250, 0.18), rgba(124, 58, 237, 0.08))',
          boxShadow: open ? '0 0 24px rgba(167, 139, 250, 0.18)' : '0 0 12px rgba(167, 139, 250, 0.08)',
          color: '#ddd6fe',
          cursor: 'pointer',
          padding: 0,
        }}
      >
        <BookOpen size={14} />
      </button>

      {open && popupStyle && typeof document !== 'undefined'
        ? createPortal(
            <div
              ref={popupRef}
              onClick={(event) => event.stopPropagation()}
              style={{
                position: 'fixed',
                top: popupStyle.top,
                left: popupStyle.left,
                width: popupStyle.width,
                maxHeight: popupStyle.maxHeight,
                overflowY: 'auto',
                overscrollBehavior: 'contain',
                WebkitOverflowScrolling: 'touch',
                padding: '1.2rem 1.15rem 2rem',
                borderRadius: '22px',
                border: '1px solid rgba(167, 139, 250, 0.24)',
                background:
                  'linear-gradient(180deg, rgba(17, 12, 27, 0.98), rgba(9, 8, 16, 0.98))',
                boxShadow: '0 30px 80px rgba(0,0,0,0.55), 0 0 30px rgba(167, 139, 250, 0.08)',
                backdropFilter: 'blur(24px)',
                textAlign: 'left',
                zIndex: 2200,
                transformOrigin: `${popupStyle.originX} 0%`,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '1rem',
                  marginBottom: '1rem',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.72rem',
                    letterSpacing: '0.16em',
                    textTransform: 'uppercase',
                    color: '#a78bfa',
                  }}
                >
                  Citations
                </div>
                <button
                  type="button"
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    setOpen(false);
                  }}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 30,
                    height: 30,
                    borderRadius: 999,
                    border: '1px solid rgba(255,255,255,0.08)',
                    background: 'rgba(255,255,255,0.03)',
                    color: '#cbd5e1',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  <X size={14} />
                </button>
              </div>

              <div style={{ display: 'grid', gap: '1rem' }}>
                {entries.map((entry, index) => (
                  <div
                    key={entry.key}
                    style={{
                      display: 'grid',
                      gap: '0.45rem',
                      paddingBottom: index < entries.length - 1 ? '1rem' : 0,
                      borderBottom: index < entries.length - 1 ? '1px solid rgba(255,255,255,0.08)' : 'none',
                    }}
                  >
                    <div
                      style={{
                        fontFamily: 'var(--font-sans)',
                        fontSize: '0.88rem',
                        lineHeight: 1.68,
                        color: '#e2e8f0',
                      }}
                    >
                      {entry.apa}
                    </div>
                    {entry.url ? (
                      <a
                        href={entry.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(event) => event.stopPropagation()}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.45rem',
                          width: 'fit-content',
                          padding: '0.5rem 0.72rem',
                          borderRadius: '999px',
                          border: '1px solid rgba(147, 197, 253, 0.28)',
                          background: 'rgba(59, 130, 246, 0.08)',
                          fontFamily: 'var(--font-sans)',
                          fontSize: '0.78rem',
                          fontWeight: 500,
                          color: '#bfdbfe',
                          textDecoration: 'none',
                        }}
                      >
                        Open source
                        <ArrowUpRight size={13} />
                      </a>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>,
            document.body,
          )
        : null}
    </span>
  );
}
