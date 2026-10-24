import type { Metadata } from "next";
import "./globals.css";
import { AppSidebar } from "@/components/layout/AppSidebar";

export const metadata: Metadata = {
    title: "NeuroSyn Sentinel Twin",
    description: "Test security and infrastructure decisions against a digital twin before applying them.",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="antialiased flex min-h-screen bg-[#FAFAFA] text-neutral-900">
                <AppSidebar />
                <main className="flex-1 min-w-0 overflow-y-auto">{children}</main>
            </body>
        </html>
    );
}