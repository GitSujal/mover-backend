"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Truck, Calendar, Settings, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
    { name: "Dashboard", href: "/mover", icon: LayoutDashboard },
    { name: "Fleet Management", href: "/mover/fleet", icon: Truck },
    { name: "Jobs & Schedule", href: "/mover/jobs", icon: Calendar },
    { name: "Settings", href: "/mover/settings", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex h-full w-64 flex-col bg-slate-900 text-white">
            <div className="flex h-16 items-center px-6">
                <span className="text-xl font-bold text-primary-400">MoveHub Partner</span>
            </div>

            <div className="flex flex-1 flex-col gap-y-4 overflow-y-auto px-4 py-4">
                <nav className="flex flex-1 flex-col gap-y-1">
                    {navigation.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={cn(
                                    "group flex items-center gap-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-primary-600 text-white"
                                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                                )}
                            >
                                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>

                <div className="mt-auto border-t border-slate-800 pt-4">
                    <button
                        className="group flex w-full items-center gap-x-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
                        onClick={() => { }}
                    >
                        <LogOut className="h-5 w-5 shrink-0" aria-hidden="true" />
                        Sign out
                    </button>
                </div>
            </div>
        </div>
    );
}
