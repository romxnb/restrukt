const dateFormat = new Intl.DateTimeFormat('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric' })

/** Formats an ISO date such as "2026-10-05" as "05.10.2026". */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return dateFormat.format(new Date(year ?? 0, (month ?? 1) - 1, day ?? 1))
}
