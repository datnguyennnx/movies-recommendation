import { Inter } from 'next/font/google';
import './globals.css';
import Layout from '@/components/layout/Layout';
import AuthWrapper from '@/components/layout/AuthWrapper';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <Layout>
                    <AuthWrapper>{children}</AuthWrapper>
                </Layout>
            </body>
        </html>
    );
}
