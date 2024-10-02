'use client';

import { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
    return (
        <div className="flex min-h-screen">
            <main className="flex-grow">{children}</main>
        </div>
    );
}
