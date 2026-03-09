import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Taiga Capital — PE Investment AI Platform",
  description:
    "AI-powered private equity investment management platform by Taiga Capital Group",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="antialiased">
        <Sidebar />
        <main className="ml-[240px] min-h-screen transition-all duration-300">
          {children}
        </main>
      </body>
    </html>
  );
}
