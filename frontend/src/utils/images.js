export function getThumbUrl(url) {
  if (!url || typeof url !== 'string') return url
  if (url.startsWith('bg:')) return url
  if (!url.startsWith('/uploads/')) return url
  if (/\.gif$/i.test(url)) return url
  return url.replace(/\.(jpg|jpeg|png|webp)$/i, '.thumb.webp')
}

export function getMediumUrl(url) {
  if (!url || typeof url !== 'string') return url
  if (url.startsWith('bg:')) return url
  if (!url.startsWith('/uploads/')) return url
  if (/\.gif$/i.test(url)) return url
  return url.replace(/\.(jpg|jpeg|png|webp)$/i, '.medium.webp')
}
