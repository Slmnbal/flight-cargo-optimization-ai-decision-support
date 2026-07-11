// Elle yazılmış, dışarıdan kütüphane eklemeyen küçük bir SVG ikon seti
// (Feather-tarzı: 24x24 viewBox, stroke=currentColor, 1.5px, yuvarlak
// uçlar). Tek bir dosyada tutuluyor -- bu ölçekte ayrı bir ikon paketi
// kurmak (npm bağımlılığı) gereksiz; 8 sabit ikon proportional bir çözüm.
import type { ReactNode, SVGProps } from 'react'

export type IconName =
  | 'overview'
  | 'database'
  | 'route'
  | 'flight'
  | 'cargo'
  | 'gauge'
  | 'chat'
  | 'chevron-right'
  | 'trend-up'

const PATHS: Record<IconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  database: (
    <>
      <ellipse cx="12" cy="5.5" rx="8" ry="3" />
      <path d="M4 5.5v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
      <path d="M4 11.5v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
    </>
  ),
  route: (
    <>
      <circle cx="5" cy="6" r="2" />
      <circle cx="19" cy="18" r="2" />
      <path d="M5 8c0 6 4 4 4 8c0 3 5 3 5 0c0-4 5-2 5-6" />
    </>
  ),
  flight: (
    <path d="M12 2.5c-.5 0-1 .4-1 1v6.4L3.6 14c-.4.3-.6.7-.6 1.1v1.4l8-2.5v4.2l-2.3 1.7v1.4l3.3-.9 3.3.9v-1.4L13 18.2V14l8 2.5v-1.4c0-.4-.2-.8-.6-1.1L13 9.9V3.5c0-.6-.5-1-1-1Z" />
  ),
  cargo: (
    <>
      <path d="M3 8.5 12 4l9 4.5-9 4.5-9-4.5Z" />
      <path d="M3 8.5V16l9 4.5 9-4.5V8.5" />
      <path d="M12 13v7.5" />
    </>
  ),
  gauge: (
    <>
      <path d="M4 15a8 8 0 1 1 16 0" />
      <path d="M12 15 15.5 10" />
      <circle cx="12" cy="15" r="1.2" fill="currentColor" stroke="none" />
    </>
  ),
  chat: (
    <path d="M4 5h16v10H8.5L4 18.5V15H4V5Z" />
  ),
  'chevron-right': <path d="M9 5l7 7-7 7" />,
  'trend-up': <path d="M4 16l5-6 4 3 7-9" />,
}

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName
  size?: number
}

export function Icon({ name, size = 18, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {PATHS[name]}
    </svg>
  )
}
