/**
 * Root Layout Component
 * Main layout wrapper for the Codegen Visual Interface
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Codegen Visual Interface',
  description: 'Visual CICD Flow Interface for Codegen with AI Chat Orchestration',
  keywords: ['codegen', 'cicd', 'workflow', 'ai', 'automation'],
  authors: [{ name: 'Codegen Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#0ea5e9',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body className={`${inter.className} antialiased`}>
        <div id="root" className="min-h-screen bg-gray-50">
          {children}
        </div>
        <div id="modal-root" />
        <div id="tooltip-root" />
      </body>
    </html>
  );
}
