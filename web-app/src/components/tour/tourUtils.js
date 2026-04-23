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

export function getTooltipPosition(rect, placement = 'bottom', hasImage = false) {
  const width = Math.min(hasImage ? 780 : 360, window.innerWidth - 32);
  const gap = 18;
  const margin = 16;
  const estimatedHeight = hasImage ? 560 : 280;
  const clampTop = (value) => Math.min(Math.max(value, margin), Math.max(margin, window.innerHeight - estimatedHeight - margin));
  const belowTop = rect ? rect.bottom + gap : null;
  const aboveTop = rect ? rect.top - gap - estimatedHeight : null;

  if (!rect || placement === 'center') {
    return {
      top: clampTop(window.innerHeight / 2 - (hasImage ? 260 : 120)),
      left: Math.max(margin, window.innerWidth / 2 - width / 2),
      width,
    };
  }

  const centeredLeft = rect.left + rect.width / 2 - width / 2;
  const clampLeft = Math.min(Math.max(centeredLeft, margin), window.innerWidth - width - margin);

  if (placement === 'top') {
    if (aboveTop !== null && aboveTop >= margin) {
      return {
        top: aboveTop,
        left: clampLeft,
        width,
      };
    }
    return {
      top: clampTop(rect.bottom + gap),
      left: clampLeft,
      width,
    };
  }

  if (placement === 'left') {
    const left = rect.left - width - gap;
    if (left >= margin) {
      return {
        top: clampTop(rect.top),
        left,
        width,
      };
    }
  }

  if (placement === 'right') {
    const left = rect.right + gap;
    if (left + width <= window.innerWidth - margin) {
      return {
        top: clampTop(rect.top),
        left,
        width,
      };
    }
  }

  const preferredTop = placement === 'bottom'
    ? (belowTop !== null && belowTop + estimatedHeight <= window.innerHeight - margin ? belowTop : aboveTop)
    : (aboveTop !== null && aboveTop >= margin ? aboveTop : belowTop);

  return {
    top: clampTop(preferredTop ?? (window.innerHeight / 2 - estimatedHeight / 2)),
    left: clampLeft,
    width,
  };
}
