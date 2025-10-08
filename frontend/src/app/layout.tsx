import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import './globals.css'

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'FlowerSight - AI Bloom Prediction with NASA Data',
  description:
    'Predict flowering times for crops using NASA satellite data and machine learning. Real-time bloom forecasting for almonds, apples, and cherries with NDVI analysis.',
  keywords: [
    'bloom prediction',
    'NASA',
    'NDVI',
    'satellite data',
    'agriculture',
    'machine learning',
    'flowering forecast',
    'crop monitoring',
  ],
  authors: [{ name: 'FlowerSight Team' }],
  openGraph: {
    title: 'FlowerSight - AI Bloom Prediction',
    description:
      'Predict flowering times for crops using NASA satellite data and AI',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'FlowerSight - AI Bloom Prediction',
    description:
      'Predict flowering times for crops using NASA satellite data and AI',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} antialiased`}>{children}</body>
    </html>
  )
}
