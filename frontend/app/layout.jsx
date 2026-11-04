import "@fontsource-variable/source-serif-4";
import "@fontsource-variable/public-sans";
import "@fontsource/mrs-saint-delafield";
import { Analytics } from "@vercel/analytics/next";
import Providers from "@/components/Providers";
import "./globals.css";

export const metadata = {
  metadataBase: new URL("https://contractiq-ten.vercel.app"),
  title: {
    default: "ContractIQ — know what you're signing",
    template: "%s · ContractIQ",
  },
  description:
    "Upload a contract and ContractIQ marks up the risky clauses, explains them in plain English, and tracks the obligations and dates you've agreed to.",
  openGraph: {
    title: "ContractIQ",
    description: "Every risky clause, highlighted and explained. Every obligation, tracked.",
    type: "website",
  },
};

export const viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#171b2c" },
  ],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-dvh">
        <Providers>{children}</Providers>
        <Analytics />
      </body>
    </html>
  );
}