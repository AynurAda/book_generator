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
  title: "Learner | Learn any field. Build what you imagine.",
  description: "Want to learn something new to build something cool? We create personalized books that teach you exactly what you need — with examples from YOUR project.",
  keywords: ["personalized learning", "custom textbooks", "learn to build", "project-based learning", "AI education"],
  openGraph: {
    title: "Learner | Learn any field. Build what you imagine.",
    description: "Personalized books that teach you exactly what you need for your project.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Learner | Learn any field. Build what you imagine.",
    description: "Personalized books that teach you exactly what you need for your project.",
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
