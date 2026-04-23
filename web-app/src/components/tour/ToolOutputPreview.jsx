export default function ToolOutputPreview({ title = 'Output Preview', summary, items = [], downloads = [] }) {
  return (
    <div className="tool-output-preview">
      <div className="tool-output-preview-label">{title}</div>
      {summary ? <p className="tool-output-preview-summary">{summary}</p> : null}

      {items.length > 0 && (
        <div className="tool-output-preview-grid">
          {items.map((item) => (
            <div key={item.title} className="tool-output-preview-item">
              <div className="tool-output-preview-item-title">{item.title}</div>
              <p className="tool-output-preview-item-copy">{item.copy}</p>
            </div>
          ))}
        </div>
      )}

      {downloads.length > 0 && (
        <div className="tool-output-preview-downloads">
          {downloads.map((download) => (
            <span key={download} className="tool-output-preview-download-chip">
              {download}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
