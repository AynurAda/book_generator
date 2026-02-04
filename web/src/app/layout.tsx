import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Polaris | Your north star to the cutting edge",
  description: "Navigate to mastery with knowledge synthesized for exactly one person — you. We collapse the decade-long knowledge pipeline so you can learn breakthroughs in time to build something that matters.",
  keywords: ["knowledge synthesis", "personalized books", "cutting edge learning", "AI education", "research to understanding"],
  openGraph: {
    title: "Polaris | Your north star to the cutting edge",
    description: "Navigate to mastery with knowledge synthesized for exactly one person — you.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Polaris | Your north star to the cutting edge",
    description: "Navigate to mastery with knowledge synthesized for exactly one person — you.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
