import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ご縁 — Goen",
  description: "ご縁を創出・持続・拡張するアプリケーション",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="font-sans min-h-screen bg-cosmos-bg antialiased">
        {children}
      </body>
    </html>
  );
}
