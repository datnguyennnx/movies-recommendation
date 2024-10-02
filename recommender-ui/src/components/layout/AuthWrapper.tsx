'use client';

import { useEffect, useState, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { isAuthenticated } from '@/lib/authUtils';

interface AuthWrapperProps {
    children: ReactNode;
}

export default function AuthWrapper({ children }: AuthWrapperProps) {
    const [authChecked, setAuthChecked] = useState(false);
    const [isAuth, setIsAuth] = useState(false);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const checkAuth = async () => {
            const auth = await isAuthenticated();
            setIsAuth(auth);
            setAuthChecked(true);
            if (!auth && pathname !== '/login') {
                router.push('/login');
            } else if (auth && pathname === '/login') {
                router.push('/');
            }
        };
        checkAuth();
    }, [router, pathname]);

    if (!authChecked) {
        return <div>Loading...</div>;
    }

    return isAuth || pathname === '/login' ? <>{children}</> : null;
}
