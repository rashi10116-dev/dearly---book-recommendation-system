import React from 'react';
import { BookOpen, Sparkles, Compass, ShieldCheck, Shuffle, ArrowRight, Star, Heart, BookmarkCheck, Check } from 'lucide-react';

export default function LandingHero({ onGetStarted, onExploreCatalogue, onDemoLogin }) {
  return (
    <div className="space-y-20 pb-20">
      
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 md:pt-20">
        <div className="max-w-5xl mx-auto text-center px-4 space-y-6">
          
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#EAE3D9] text-[#571B37] text-xs font-semibold tracking-wide">
            <Sparkles className="w-3.5 h-3.5 text-[#C48332]" />
            Personalized Discovery Inspired by Music Streaming Mixes
          </div>

          <h1 className="font-editorial text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight text-[#2A0F1D] leading-[1.08]">
            Don't just find a book.<br />
            <span className="italic font-normal text-[#571B37]">Find your next favorite.</span>
          </h1>

          <p className="text-base sm:text-lg text-[#695D56] max-w-2xl mx-auto leading-relaxed">
            DEARLY learns your unique narrative taste—blending your favorite tropes, writing styles, pacing, and emotional tones to uncover books you’ll genuinely cherish, while breaking free from bestseller popularity bias.
          </p>

          {/* Call to Actions */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <button
              onClick={onGetStarted}
              className="px-7 py-3.5 rounded-2xl bg-[#571B37] hover:bg-[#3D1426] text-white text-sm font-bold shadow-lg shadow-[#571B37]/20 transition-all hover:scale-102 cursor-pointer flex items-center gap-2"
            >
              Start Personalizing
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onExploreCatalogue}
              className="px-6 py-3.5 rounded-2xl bg-white hover:bg-[#F5EFEB] border border-[#EAE3D9] text-[#2A0F1D] text-sm font-semibold shadow-xs transition-all cursor-pointer flex items-center gap-2"
            >
              <Compass className="w-4 h-4 text-[#571B37]" />
              Explore Catalogue
            </button>

            <button
              onClick={onDemoLogin}
              className="px-5 py-3.5 rounded-2xl bg-[#E09E4B]/15 hover:bg-[#E09E4B]/25 text-[#925514] text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#C48332]" />
              Instant Demo Account
            </button>
          </div>

        </div>

        {/* Visual Showcase: Curated Book Mixes Preview */}
        <div className="mt-14 max-w-6xl mx-auto px-4">
          <div className="bg-gradient-to-b from-[#FAF7F2] to-white p-6 sm:p-8 rounded-3xl border border-[#EAE3D9] shadow-xl space-y-6">
            
            <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#C48332] block">Discovery Deck Preview</span>
                <h3 className="font-editorial text-2xl font-bold text-[#2A0F1D]">Your Daily Personalized Mixes</h3>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-[#EAE3D9] text-[#571B37] font-semibold hidden sm:inline-block">
                Powered by TF-IDF & MMR Vector Ranking
              </span>
            </div>

            {/* 3 Showcase Mix Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Mix 1: Your Taste */}
              <div className="bg-[#FCFAF6] p-5 rounded-2xl border border-[#EAE3D9] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#571B37] flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-[#C48332]" />
                    Your Taste: Dark Academia
                  </span>
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#571B37]/10 text-[#571B37]">96% Match</span>
                </div>
                <div className="flex gap-3 items-center">
                  <img
                    src="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80"
                    alt="The Secret History"
                    className="w-16 h-24 object-cover rounded-xl shadow-md border border-[#EAE3D9]"
                  />
                  <div>
                    <h4 className="font-editorial font-bold text-base text-[#2A0F1D]">The Secret History</h4>
                    <p className="text-xs text-[#7A6E65]">Donna Tartt</p>
                    <p className="text-[11px] text-[#2A533E] font-medium mt-1 flex items-center">
                      <Check className="w-3 h-3 text-[#2A533E] inline mr-1 shrink-0" />
                      Secret Society, Moral Decay
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-[#7A6E65] italic bg-white p-2.5 rounded-xl border border-[#EAE3D9]">
                  "Ranked for your taste in Dark Academia — aligns with Lyrical writing and Slow Burn pacing."
                </p>
              </div>

              {/* Mix 2: Your Unexpected Next Read */}
              <div className="bg-[#FCFAF6] p-5 rounded-2xl border border-[#EAE3D9] space-y-3 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-[#E09E4B]/10 rounded-full blur-2xl pointer-events-none" />
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#C48332] flex items-center gap-1">
                    <Shuffle className="w-3.5 h-3.5" />
                    Unexpected Discovery
                  </span>
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#E09E4B]/20 text-[#8C5819]">Serendipity</span>
                </div>
                <div className="flex gap-3 items-center">
                  <img
                    src="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=400&q=80"
                    alt="Before the Coffee Gets Cold"
                    className="w-16 h-24 object-cover rounded-xl shadow-md border border-[#EAE3D9]"
                  />
                  <div>
                    <h4 className="font-editorial font-bold text-base text-[#2A0F1D]">Before the Coffee Gets Cold</h4>
                    <p className="text-xs text-[#7A6E65]">Toshikazu Kawaguchi</p>
                    <p className="text-[11px] text-[#8C5819] font-medium mt-1 flex items-center">
                      <Sparkles className="w-3 h-3 text-[#8C5819] inline mr-1 shrink-0" />
                      Hidden Gem (Anti-Popularity)
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-[#7A6E65] italic bg-white p-2.5 rounded-xl border border-[#EAE3D9]">
                  "Outside your usual shelf, this Magical Realism tale shares your love for quiet, contemplative second chances."
                </p>
              </div>

              {/* Mix 3: Because You Enjoyed */}
              <div className="bg-[#FCFAF6] p-5 rounded-2xl border border-[#EAE3D9] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#1C3829] flex items-center gap-1">
                    <BookmarkCheck className="w-3.5 h-3.5 text-[#2A533E]" />
                    Because You Enjoyed...
                  </span>
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#2A533E]/10 text-[#1C3829]">Story DNA</span>
                </div>
                <div className="flex gap-3 items-center">
                  <img
                    src="https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=400&q=80"
                    alt="Six of Crows"
                    className="w-16 h-24 object-cover rounded-xl shadow-md border border-[#EAE3D9]"
                  />
                  <div>
                    <h4 className="font-editorial font-bold text-base text-[#2A0F1D]">Six of Crows</h4>
                    <p className="text-xs text-[#7A6E65]">Leigh Bardugo</p>
                    <p className="text-[11px] text-[#571B37] font-medium mt-1 flex items-center">
                      <Check className="w-3 h-3 text-[#571B37] inline mr-1 shrink-0" />
                      Found Family, Morally Grey
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-[#7A6E65] italic bg-white p-2.5 rounded-xl border border-[#EAE3D9]">
                  "Recommended because you loved complex ensemble heist dynamics with high emotional stakes."
                </p>
              </div>

            </div>

          </div>
        </div>
      </section>

      {/* Feature Pillars: Why DEARLY */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="font-editorial text-3xl sm:text-4xl font-bold text-[#2A0F1D]">
            Rethinking Book Recommendations
          </h2>
          <p className="text-sm text-[#695D56] mt-2">
            Most book sites push what is already famous. DEARLY uncovers what is right for you.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          <div className="bg-white p-7 rounded-3xl border border-[#EAE3D9] space-y-3 shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-[#571B37]/10 text-[#571B37] flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">Anti-Popularity Bias</h3>
            <p className="text-xs text-[#695D56] leading-relaxed">
              Mainstream platforms optimize for bestsellers. DEARLY balances familiar favorites with lesser-known titles and indie gems based on genuine literary resonance.
            </p>
          </div>

          <div className="bg-white p-7 rounded-3xl border border-[#EAE3D9] space-y-3 shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-[#C48332]/10 text-[#C48332] flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">Trope & Texture Matching</h3>
            <p className="text-xs text-[#695D56] leading-relaxed">
              Beyond surface genres, we index narrative DNA: <em>Enemies to Lovers</em>, <em>Found Family</em>, writing pace, emotional tone, and prose style.
            </p>
          </div>

          <div className="bg-white p-7 rounded-3xl border border-[#EAE3D9] space-y-3 shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-[#2A533E]/10 text-[#2A533E] flex items-center justify-center">
              <Shuffle className="w-6 h-6" />
            </div>
            <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">Serendipitous Discovery</h3>
            <p className="text-xs text-[#695D56] leading-relaxed">
              Find surprising cross-genre books. If you love political intrigue and complex grey morality in Fantasy, discover historical fiction that shares that exact tension.
            </p>
          </div>

        </div>
      </section>

    </div>
  );
}
