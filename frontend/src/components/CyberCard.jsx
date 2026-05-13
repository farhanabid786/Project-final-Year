import React from 'react';

const CyberCard = ({ title, description, type, onAction }) => {
    // SVG paths for our 3 specific modes
    const getIcon = () => {
        switch (type) {
            case 'image':
                return <path d="M5 19l5-5 3 3 5-5 2 2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z" strokeWidth="1.5" />;
            case 'video':
                return <path d="M23 7l-7 5 7 5V7z M1 5h11a2 2 0 012 2v10a2 2 0 01-2 2H1a2 2 0 01-2-2V7a2 2 0 012-2z" strokeWidth="1.5" />;
            case 'live':
                return (
                    <>
                        <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" strokeWidth="1.5" />
                        <circle cx="12" cy="12" r="3" fill="#FF6F37" className="animate-pulse" />
                    </>
                );
            default:
                return <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeWidth="1.5" />;
        }
    };

    return (
        <div className="card">


            <figure className="card__figure flex items-center justify-center">
                {/* icon container: reduced to 64px for a sharper look */}
                <div className="w-48 h-48 flex items-center justify-center">
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#FF6F37"
                        strokeWidth="1.1" /* Thinner lines = cleaner tech vibe */
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="w-full h-full"
                    >
                        {getIcon()}
                    </svg>
                </div>
            </figure>

            <div className="card__info">
                <h3 className="card__name">{title}</h3>
                <p className="card__ocupation text-xs mt-2">{description}</p>

                <button
                    onClick={onAction}
                    className="mt-6 px-5 py-2 border border-[#FF6F37] text-[#FF6F37] rounded-md hover:bg-[#FF6F37] hover:text-black transition-all duration-300 font-bold tracking-tighter text-[10px]"
                >
                    LAUNCH MODULE
                </button>
            </div>
        </div>
    );
};

export default CyberCard;