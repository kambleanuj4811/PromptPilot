// The backend stores UTC but may omit the zone marker, so add it before parsing.
export function formatTime(iso) {
  if (!iso) return ''
  const hasZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(iso)
  const d = new Date(hasZone ? iso : `${iso}Z`)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleString()
}