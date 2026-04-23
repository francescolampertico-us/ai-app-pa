export function getTourTarget(target) {
  if (!target) return null;
  return document.querySelector(`[data-tour="${target}"]`);
}

export function scrollTargetIntoView(element) {
  if (!element) return;

  const rect = element.getBoundingClientRect();
  const viewportPadding = 24;
  const inView =
    rect.top >= viewportPadding &&
    rect.left >= viewportPadding &&
    rect.bottom <= window.innerHeight - viewportPadding &&
    rect.right <= window.innerWidth - viewportPadding;

  if (!inView) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
  }
}

export function getTooltipPosition(rect, placement = 'bottom') {
  const width = Math.min(360, window.innerWidth - 32);
  const gap = 18;
  const margin = 16;

  if (!rect || placement === 'center') {
    return {
      top: Math.max(margin, window.innerHeight / 2 - 120),
      left: Math.max(margin, window.innerWidth / 2 - width / 2),
      width,
    };
  }

  const centeredLeft = rect.left + rect.width / 2 - width / 2;
  const clampLeft = Math.min(Math.max(centeredLeft, margin), window.innerWidth - width - margin);

  if (placement === 'top') {
    return {
      top: Math.max(margin, rect.top - gap - 168),
      left: clampLeft,
      width,
    };
  }

  if (placement === 'left') {
    const left = rect.left - width - gap;
    if (left >= margin) {
      return {
        top: Math.min(Math.max(rect.top, margin), window.innerHeight - 200),
        left,
        width,
      };
    }
  }

  if (placement === 'right') {
    const left = rect.right + gap;
    if (left + width <= window.innerWidth - margin) {
      return {
        top: Math.min(Math.max(rect.top, margin), window.innerHeight - 200),
        left,
        width,
      };
    }
  }

  const preferredTop = placement === 'bottom'
    ? rect.bottom + gap
    : rect.top - gap - 168;

  return {
    top: Math.min(Math.max(preferredTop, margin), window.innerHeight - 184),
    left: clampLeft,
    width,
  };
}
