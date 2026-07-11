import type { ReactNode } from 'react'

export interface DataTableColumn<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  align?: 'left' | 'right'
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  isLoading?: boolean
  emptyLabel?: string
}

export function DataTable<T>({ columns, rows, rowKey, isLoading, emptyLabel = 'Kayıt bulunamadı.' }: DataTableProps<T>) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-max text-left text-sm">
        <thead>
          <tr className="border-b border-border text-xs uppercase tracking-wide text-ink-muted">
            {columns.map((col) => (
              <th key={col.key} className={`px-4 py-3 font-medium ${col.align === 'right' ? 'text-right' : 'text-left'}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-6 text-center text-ink-muted">
                Yükleniyor...
              </td>
            </tr>
          )}
          {!isLoading && rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-6 text-center text-ink-muted">
                {emptyLabel}
              </td>
            </tr>
          )}
          {!isLoading &&
            rows.map((row) => (
              <tr key={rowKey(row)} className="border-b border-border last:border-0 hover:bg-surface-alt">
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3 text-ink ${col.align === 'right' ? 'text-right' : 'text-left'}`}>
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
