'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useRouter, useSearchParams } from 'next/navigation';
import { initiateGoogleAuth, isAuthenticated } from '@/lib/authUtils';
import { FcGoogle } from 'react-icons/fc';

export default function LoginPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const error = searchParams.get('error');

    useEffect(() => {
        const checkAuth = async () => {
            const auth = await isAuthenticated();
            if (auth) {
                router.push('/');
            }
        };
        checkAuth();
    }, [router]);

    const handleLogin = async () => {
        try {
            await initiateGoogleAuth();
        } catch (error) {
            console.error('Error initiating Google auth:', error);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="w-full max-w-md p-8 space-y-4 ">
                <h1 className="text-2xl font-bold text-center mb-8 text-nowrap">
                    Log in to Movie Recommender
                </h1>

                <Button
                    onClick={handleLogin}
                    className="w-full bg-white hover:bg-gray-100 border text-black flex items-center justify-center space-x-2 py-6 rounded-md transition duration-300 ease-in-out"
                >
                    <FcGoogle className="w-5 h-5 " />
                    <span>Continue with Google</span>
                </Button>

                {error && (
                    <p className="text-red-500 text-center mt-4">
                        Authentication failed. Please try again.
                    </p>
                )}
            </div>
        </div>
    );
}
