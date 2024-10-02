import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const token = searchParams.get('token');

    if (!token) {
        return NextResponse.redirect(
            new URL('/login?error=missing_token', request.url)
        );
    }

    // Create a response that redirects to the home page with the token in the URL
    const response = NextResponse.redirect(
        new URL(`/?token=${token}`, request.url)
    );

    // Set the token in a cookie
    response.cookies.set('token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24, // 1 day
        path: '/',
    });

    return response;
}
