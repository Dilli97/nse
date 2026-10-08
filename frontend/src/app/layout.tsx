import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "NSE Analysis",
  description: "Stock Analysis Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-blue-900 text-white p-4">
            <h1 className="text-xl font-bold">NSE Analysis Platform</h1>
        </nav>
        <main className="container mx-auto p-4">
            {children}
        </main>
      </body>
    </html>
  );
}
