interface LogoProps {
    hasText?: boolean;
}

export const LogoDwarves = (props: LogoProps) => {
    const { hasText = false } = props;

    return (
        <div className="flex items-center justify-center">
            <svg height="41" viewBox="0 0 39 41" width="39">
                <title>Logo Dwarves</title>
                <g fill="none" fillRule="nonzero">
                    <path
                        d="M5.208 40.726c-2.804 0-5.074-2.279-5.074-5.093V5.093C.134 2.278 2.404 0 5.208 0l12.703.015c11.292 0 20.433 9.262 20.285 20.623-.149 11.183-9.438 20.088-20.582 20.088H5.208z"
                        fill="#E13F5E"
                    />
                    <path
                        d="M7.76 31.821h-.652a.634.634 0 0 1-.638-.64v-5.108c0-.357.282-.64.638-.64h5.09c.356 0 .638.283.638.64v.655c0 2.815-2.27 5.093-5.075 5.093zM7.108 16.528H22.97c2.804 0 5.075-2.278 5.075-5.092v-.61a.666.666 0 0 0-.668-.67H11.56c-2.805 0-5.075 2.278-5.075 5.092v.64c0 .358.282.64.623.64zM7.108 24.167h8.25c2.805 0 5.075-2.278 5.075-5.092v-.64a.634.634 0 0 0-.638-.64H7.108a.634.634 0 0 0-.638.64v5.092c.015.357.297.64.638.64z"
                        fill="#FFF"
                    />
                </g>
            </svg>
            {hasText && (
                <div className="text-white text-2xl tracking-wide ml-3 font-semibold">
                    dwarvesf
                </div>
            )}
        </div>
    );
};

export const LogoUser = (props: LogoProps) => {
    const { hasText = false } = props;

    return (
        <div className="flex items-center justify-center">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                version="1.0"
                width="39.000000pt"
                height="39.000000pt"
                viewBox="0 0 39 39"
                preserveAspectRatio="xMidYMid meet"
            >
                <g
                    transform="matrix(.1 0 0 -.1 0 39)"
                    fill="#000000"
                    stroke="none"
                >
                    <path d="M100.623 389.01c-6.17 -3.123 -8.379 -15.31 -8.912 -50.045l-0.381 -20.185 -2.59 -5.103c-6.703 -12.72 -8.607 -21.252 -9.598 -42.504 -1.371 -30.621 -4.647 -39.685 -25.365 -70.764 -13.711 -20.567 -20.871 -33.44 -25.518 -46.008 -10.74 -28.945 -10.055 -59.719 1.828 -84.855 12.568 -26.584 36.943 -45.322 74.42 -57.205C131.092 3.808 156.762 0.457 195 0.457s63.908 3.352 90.492 11.883c41.361 13.102 66.879 34.658 78.076 65.813 4.037 11.35 5.485 20.719 5.408 36.105 0 12.568 -0.228 15.082 -2.133 23.004 -4.647 20.185 -11.959 35.192 -30.621 63.147 -20.719 31.078 -23.994 40.143 -25.365 70.764 -0.99 21.252 -2.895 29.783 -9.598 42.504l-2.59 5.103 -0.381 20.185c-0.685 41.285 -3.732 52.558 -14.015 50.655 -5.789 -1.067 -20.947 -19.957 -28.869 -36.03 -0.076 -0.152 -2.514 0.61 -5.56 1.675 -21.328 7.693 -46.313 11.425 -64.898 9.674 -15.996 -1.447 -31.23 -4.799 -44.789 -9.674 -3.047 -1.067 -5.485 -1.828 -5.56 -1.675 -4.19 8.379 -14.32 23.385 -19.805 29.326 -6.17 6.627 -9.978 8.227 -14.168 6.094m17.977 -31.84c2.818 -4.342 5.256 -8.15 5.408 -8.379 0.152 -0.305 -2.438 -2.133 -5.637 -4.113 -3.2 -2.057 -7.845 -5.332 -10.283 -7.389l-4.494 -3.732v4.037c0.076 6.627 1.447 30.545 1.98 33.973l0.533 3.2 3.58 -4.875c2.057 -2.59 6.018 -8.379 8.912 -12.72m167.045 -1.828c0.381 -7.922 0.762 -16.148 0.762 -18.129v-3.656l-4.494 3.732c-2.438 2.057 -7.084 5.332 -10.283 7.313 -3.2 2.057 -5.789 3.732 -5.789 3.885 0 0.381 12.72 19.195 15.235 22.547l2.666 3.504 0.533 -2.361c0.305 -1.295 0.914 -8.836 1.371 -16.834m-76.781 -3.047c18.738 -2.209 32.906 -6.246 48.217 -13.711 28.26 -13.863 41.514 -35.115 41.514 -66.575 0 -18.662 2.742 -32.525 9.522 -47.836 4.57 -10.36 6.094 -12.95 20.567 -34.277 14.625 -21.785 22.928 -39.457 26.736 -57.357 2.133 -9.75 1.98 -29.935 -0.305 -39.381 -6.322 -26.432 -20.643 -44.408 -46.617 -58.348 -30.621 -16.453 -79.371 -24.603 -131.168 -22.014 -33.744 1.752 -59.643 6.627 -81.656 15.463 -34.277 13.711 -53.473 34.201 -60.785 64.898 -2.285 9.445 -2.438 29.631 -0.305 39.381 3.808 17.9 12.111 35.572 26.736 57.357 14.473 21.328 15.996 23.918 20.567 34.277 6.78 15.31 9.522 29.174 9.522 47.836 0 31.383 13.254 52.711 41.514 66.575 14.93 7.313 29.555 11.502 47.607 13.711 10.969 1.371 16.986 1.371 28.336 0" />
                    <path d="M106.26 279.55c-5.256 -2.209 -8.379 -8.607 -8.379 -17.52 0 -5.56 0.305 -7.084 2.133 -10.817 4.875 -9.902 14.549 -9.978 19.576 -0.152 1.6 3.2 1.905 4.799 1.905 10.969 0 6.703 -0.152 7.541 -2.361 11.35 -3.275 5.865 -8.15 8.15 -12.873 6.17" />
                    <path d="M275.818 278.942c-1.6 -0.838 -3.504 -3.047 -4.951 -5.56 -2.209 -3.808 -2.361 -4.647 -2.361 -11.35 0 -6.17 0.305 -7.77 1.905 -10.969 5.027 -9.826 14.701 -9.75 19.576 0.152 1.828 3.732 2.133 5.256 2.133 10.817s-0.305 7.084 -2.133 10.664c-1.143 2.285 -2.97 4.799 -4.037 5.637 -2.895 2.057 -7.084 2.361 -10.131 0.61" />
                    <path d="M183.193 254.719c-24.985 -3.428 -42.275 -15.158 -50.883 -34.582 -4.037 -9.293 -3.961 -7.008 -3.961 -85.693 0 -78.838 -0.152 -76.172 4.037 -84.55 2.438 -4.951 10.131 -12.568 15.31 -15.158 7.693 -3.885 11.273 -4.265 47.303 -4.265s39.61 0.381 47.303 4.265c5.18 2.59 12.873 10.207 15.31 15.158 4.19 8.379 4.037 5.713 4.037 84.55 0 78.685 0.076 76.4 -3.961 85.693 -6.17 13.94 -18.129 25.06 -32.373 30.164 -9.065 3.275 -14.701 4.19 -27.27 4.494 -6.932 0.152 -13.558 0.152 -14.853 -0.076m24.375 -12.568c7.313 -0.99 17.748 -4.57 22.852 -7.845 8.607 -5.56 16.53 -17.063 18.586 -26.965 0.533 -2.742 0.838 -23.156 0.838 -62.994 0 -55.682 -0.076 -59.033 -1.295 -59.033 -11.502 0.076 -31.688 3.428 -39.381 6.55 -7.845 3.2 -8.075 3.58 -8.075 14.853 0 5.637 -0.381 10.588 -0.838 11.655 -1.98 4.19 -8.531 4.19 -10.512 0 -0.457 -1.067 -0.838 -6.018 -0.838 -11.655 0 -11.273 -0.228 -11.655 -8.075 -14.853 -7.693 -3.123 -27.879 -6.475 -39.305 -6.55 -1.295 0 -1.371 3.352 -1.371 59.033 0 39.838 0.305 60.252 0.838 62.994 2.057 9.902 9.978 21.405 18.586 26.965 4.799 3.047 15.615 6.932 21.938 7.845 6.78 0.914 19.272 0.99 26.05 0m-8.912 -158.742c3.885 -2.59 12.797 -5.56 21.48 -7.236 6.627 -1.295 22.318 -3.047 27.727 -3.047h2.209l-0.381 -5.942c-0.61 -10.435 -5.485 -18.053 -14.244 -22.166l-4.265 -1.98h-72.363l-4.265 1.98c-8.76 4.113 -13.635 11.73 -14.244 22.166l-0.381 5.942h2.209c5.408 0 21.1 1.752 27.727 3.047 8.76 1.675 17.672 4.723 21.328 7.236 3.352 2.285 3.961 2.285 7.465 0" />
                    <path d="M159.047 200.256c-3.58 -0.99 -8.455 -5.18 -10.055 -8.683 -1.675 -3.504 -1.675 -9.369 -0.076 -12.873 1.828 -3.885 6.78 -8.075 9.445 -8.075 5.637 0 7.922 6.855 3.656 11.273 -1.143 1.143 -2.057 2.666 -2.057 3.275 0 1.523 2.438 3.732 4.037 3.732 0.685 0 3.58 -3.275 6.55 -7.541 2.97 -4.113 6.932 -8.912 8.912 -10.588 9.217 -8.15 21.861 -8.15 31.078 0 1.98 1.675 5.942 6.475 8.912 10.588 5.485 7.845 6.932 8.76 9.293 6.17 1.828 -1.98 1.6 -3.123 -0.762 -5.637 -4.265 -4.418 -1.98 -11.273 3.656 -11.273 2.666 0 7.617 4.19 9.445 8.075 1.6 3.504 1.6 9.369 -0.076 12.873 -2.895 6.094 -11.425 10.435 -17.977 9.217 -3.504 -0.61 -8.303 -4.799 -12.72 -11.121 -8.912 -12.72 -13.635 -15.31 -20.567 -11.35 -2.666 1.523 -3.732 2.666 -11.273 12.797 -6.703 8.988 -11.655 11.273 -19.424 9.14" />
                    <path d="M161.332 71.982c-2.514 -1.371 -3.428 -4.875 -1.98 -7.693 1.219 -2.666 8.836 -6.55 15.31 -7.998s34.201 -1.447 40.675 0 14.092 5.332 15.31 7.998c1.447 2.895 0.533 6.322 -2.133 7.693 -2.97 1.523 -3.2 1.523 -8.607 -1.143 -6.094 -2.895 -12.111 -3.808 -24.908 -3.808s-18.815 0.914 -24.908 3.808c-5.332 2.59 -5.942 2.666 -8.76 1.143" />
                </g>
            </svg>
            {hasText && (
                <div className="text-white text-2xl tracking-wide ml-3 font-semibold">
                    avatar
                </div>
            )}
        </div>
    );
};