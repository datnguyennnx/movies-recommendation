import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get('code');

    if (!code) {
        return NextResponse.json(
            { error: 'Missing code parameter' },
            { status: 400 }
        );
    }

    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';

    try {
        const response = await fetch(
            `${backendUrl}/auth/callback?code=${code}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // You might want to set cookies here based on the backend response

        return NextResponse.json(data);
    } catch (error) {
        console.error('Error exchanging code for token:', error);
        return NextResponse.json(
            { error: 'Authentication failed' },
            { status: 500 }
        );
    }
}
