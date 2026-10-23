import type { Metadata } from "next";
import "./styles.css";
export const metadata: Metadata = { title: "Scholarship Finder", description: "Evidence-grounded study funding research" };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
