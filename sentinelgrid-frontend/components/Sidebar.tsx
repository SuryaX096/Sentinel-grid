"use client";
import { ShieldHalf, Radar, ListChecks, BookOpenText } from "lucide-react";

const NAV = [
  { label: "Console", icon: Radar, href: "#" },
  { label: "Alerts", icon: ListChecks, href: "#" },
  { label: "Playbooks", icon: BookOpenText, href: "#" },
];

export default function Sidebar() {
  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex items-center gap-2 px-5 py-5">
        <ShieldHalf className="h-6 w-6 text-signal-intel" />
        <span className="font-semibold tracking-tight">SentinelGrid</span>
      </div>
      <nav className="flex flex-col gap-1 px-3">
        {NAV.map(({ label, icon: Icon, href }) => (
          <a
            key={label}
            href={href}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted transition hover:bg-raised hover:text-foreground"
          >
            <Icon className="h-4 w-4" />
            {label}
          </a>
        ))}
      </nav>
      <div className="mt-auto flex items-center gap-2 px-5 py-4 text-xs text-muted">
        <span className="h-2 w-2 animate-pulse-slow rounded-full bg-signal-safe" />
        3 agents online
      </div>
    </aside>
  );
}
