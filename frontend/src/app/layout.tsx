import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppLayout } from "@/components/layout/AppLayout";
import { ConnectionProvider } from "@/lib/providers/ConnectionProvider";
import { PwaProvider } from "@/components/pwa/PwaProvider";

const inter = Inter({ subsets: ["latin"] });

export const viewport: Viewport = {
  themeColor: "#09090b",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export const metadata: Metadata = {
  title: "DWRMS | Digital Work and Resource Management System",
  description: "Bikita Minerals Enterprise Operations & Work Management Platform",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "DWRMS",
  },
  icons: {
    icon: "/favicon.ico",
    apple: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ConnectionProvider>
          <PwaProvider>
            <AppLayout>{children}</AppLayout>
          </PwaProvider>
        </ConnectionProvider>
      </body>
    </html>
  );
}
