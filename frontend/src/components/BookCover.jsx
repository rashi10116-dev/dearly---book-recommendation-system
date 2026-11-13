import React, { useState } from 'react';
import { BookOpen } from 'lucide-react';

export default function BookCover({
  src,
  title,
  author,
  genre,
  className = '',
  aspectRatio = 'aspect-[2/3]'
}) {
  const [imageError, setImageError] = useState(false);

  const hasValidImage = Boolean(src && !imageError && src.trim() !== '');

  if (hasValidImage) {
    return (
      <img
        src={src}
        alt={title || 'Book cover'}
        onError={() => setImageError(true)}
        className={`${className} w-full h-full object-cover transition-transform duration-300`}
        loading="lazy"
      />
    );
  }

  // Elegant typographic fallback cover
  return (
    <div
      className={`w-full h-full ${aspectRatio} bg-gradient-to-br from-[#3D1426] via-[#571B37] to-[#2A0F1D] text-white p-3.5 flex flex-col justify-between shadow-inner select-none ${className}`}
      title={`${title} by ${author}`}
    >
      <div className="flex items-center justify-between opacity-80">
        <span className="text-[9px] uppercase tracking-wider font-semibold font-mono truncate max-w-[80%]">
          {genre || 'DEARLY'}
        </span>
        <BookOpen className="w-3.5 h-3.5 text-[#E09E4B] shrink-0" />
      </div>

      <div className="my-auto py-2">
        <h4 className="font-editorial text-xs sm:text-sm font-bold leading-snug line-clamp-3 text-[#FAF7F2]">
          {title || 'Untitled'}
        </h4>
        <p className="text-[10px] text-[#E09E4B] mt-1 font-medium line-clamp-1">
          {author || 'Unknown'}
        </p>
      </div>

      <div className="border-t border-white/15 pt-1.5 flex items-center justify-between text-[8px] tracking-wider uppercase text-white/60">
        <span>Edition</span>
        <span className="font-mono">DEARLY</span>
      </div>
    </div>
  );
}

