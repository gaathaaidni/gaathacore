import type { Metadata } from 'next';
import './globals.css';
import { CookieConsent } from '@/components/cookie-consent';
import { LegalFooter } from '@/components/legal-footer';

export const metadata: Metadata = {
  title: 'Sentira AI — Intelligent Video Monitoring & Visual Intelligence',
  description:
    'Sentira AI transforms CCTV camera feeds into intelligent visual monitoring, helping organizations detect relevant events and act on what matters.',
  openGraph: {
    title: 'Sentira AI — Intelligent Video Monitoring & Visual Intelligence',
    description:
      'Sentira AI transforms CCTV camera feeds into intelligent visual monitoring, helping organizations detect relevant events and act on what matters.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}<CookieConsent /><LegalFooter /></body>
    </html>
  );
}
