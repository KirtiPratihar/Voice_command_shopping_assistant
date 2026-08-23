'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Check,
  ChevronRight,
  Mic,
  MoonStar,
  Plus,
  Search,
  ShoppingBag,
  Sparkles,
  SunMedium,
  Trash2,
  Wallet,
} from 'lucide-react';
import { useTheme } from 'next-themes';
import SegmentedToggle from '../components/SegmentedToggle';

type CartItem = {
  id: string;
  name: string;
  category: 'Dairy' | 'Produce' | 'Bakery';
  quantity: number;
  price: number;
  checked: boolean;
};

type Suggestion = {
  title: string;
  note: string;
  accent: 'deal' | 'substitute' | 'alert';
};

type BackendResponse = {
  cart?: CartItem[];
  recommendations?: string[];
  suggestions?: Suggestion[];
  message?: string;
  status?: string;
  action?: string;
};

const defaultCart: CartItem[] = [
  { id: 'milk', name: 'Organic Milk', category: 'Dairy', quantity: 2, price: 3.49, checked: false },
  { id: 'avocado', name: 'Avocado', category: 'Produce', quantity: 1, price: 1.99, checked: false },
  { id: 'bread', name: 'Whole Grain Bread', category: 'Bakery', quantity: 1, price: 2.89, checked: true },
];

const defaultSuggestions: Suggestion[] = [
  { title: 'Seasonal pick', note: 'Citrus is 18% off this week.', accent: 'deal' },
  { title: 'Smart substitute', note: 'Almond milk is a strong match for dairy shoppers.', accent: 'substitute' },
  { title: 'Low stock alert', note: 'Eggs are trending fast in your usual basket.', accent: 'alert' },
];

const categories = ['All', 'Dairy', 'Produce', 'Bakery'] as const;

export default function Page() {
  const { resolvedTheme, setTheme } = useTheme();
  const [transcript, setTranscript] = useState('Say “Add two milk cartons and a loaf of bread”.');
  const [isListening, setIsListening] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>(defaultCart);
  const [suggestions, setSuggestions] = useState<Suggestion[]>(defaultSuggestions);
  const [statusMessage, setStatusMessage] = useState('Voice assistant ready.');
  const [activeFilter, setActiveFilter] = useState<(typeof categories)[number]>('All');
  const [budget, setBudget] = useState(60);
  const [preference, setPreference] = useState<'budget' | 'premium'>('budget');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setStatusMessage('Speech recognition is not supported in this browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      const results = Array.from(event.results);
      const latest = results
        .map((result: any) => result[0]?.transcript ?? '')
        .join(' ')
        .trim();

      if (latest) {
        setTranscript(latest);
      }
    };

    recognition.onerror = () => {
      setStatusMessage('Microphone access is unavailable right now.');
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    return () => recognition.stop();
  }, []);

  const subtotal = useMemo(
    () => cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [cartItems],
  );

  const visibleItems = useMemo(() => {
    if (activeFilter === 'All') return cartItems;
    return cartItems.filter((item) => item.category === activeFilter);
  }, [activeFilter, cartItems]);

  const progressPercent = Math.min((subtotal / budget) * 100, 100);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      setStatusMessage('Speech recognition is not available in this browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    recognitionRef.current.start();
    setStatusMessage('Listening for your next shopping command...');
  };

  const finalizeCommand = async (command: string) => {
    const trimmed = command.trim();
    if (!trimmed) return;

    setStatusMessage('Sending command to your smart cart...');

    try {
      const response = await fetch('https://voice-command-shopping-assistant-3zue.onrender.com/api/voice-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: trimmed,
          current_cart: cartItems,
        preference,
      }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = (await response.json()) as BackendResponse;

      if (data.cart && Array.isArray(data.cart)) {
        const mapped = data.cart.map((item) => ({
          id: String(item.id ?? item.name),
          name: item.name,
          category: item.category,
          quantity: Number(item.quantity ?? 1),
          price: Number(item.price ?? 0),
          checked: Boolean(item.checked),
        }));
        setCartItems(mapped);
      }

      if (data.suggestions && Array.isArray(data.suggestions)) {
        setSuggestions(data.suggestions as Suggestion[]);
      }

      if (data.recommendations && Array.isArray(data.recommendations)) {
        setSuggestions(
          data.recommendations.map((item, index) => ({
            title: item,
            note: index === 0 ? 'Suggested from the latest command.' : 'Derived from smart product matching.',
            accent: index % 2 === 0 ? 'deal' : 'substitute',
          })),
        );
      }

      setStatusMessage(data.message ?? data.status ?? 'Shopping command processed successfully.');
      setTranscript(trimmed);
    } catch (error) {
      console.error(error);
      setStatusMessage('The backend is offline. Local cart is still updated in demo mode.');
    }
  };

  const handleVoiceSubmit = () => finalizeCommand(transcript);

  const handleToggleItem = (itemId: string) => {
    setCartItems((previous) =>
      previous.map((item) => (item.id === itemId ? { ...item, checked: !item.checked } : item)),
    );
  };

  const handleRemoveItem = (itemId: string) => {
    setCartItems((previous) => previous.filter((item) => item.id !== itemId));
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.18),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(236,72,153,0.16),_transparent_32%),linear-gradient(to_bottom,_#f8fafc,_#eef2ff)] text-slate-900 transition-colors duration-300 dark:bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.25),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.18),_transparent_24%),linear-gradient(to_bottom,_#020617,_#0f172a)] dark:text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="orb orb-one" />
        <div className="orb orb-two" />
        <div className="orb orb-three" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-6 flex items-center justify-between gap-4 rounded-[28px] border border-white/10 bg-white/25 px-5 py-4 shadow-glass backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-300">
              Voice Commerce
            </p>
            <h1 className="mt-1 text-2xl font-semibold">Shopping Assistant</h1>
          </div>

          <div className="flex items-center gap-3">
            <SegmentedToggle value={preference} onChange={(v) => setPreference(v)} />

            <button
              type="button"
              onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/60 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm backdrop-blur-md transition hover:scale-[1.02] dark:border-white/10 dark:bg-white/5 dark:text-slate-200"
            >
              {resolvedTheme === 'dark' ? <SunMedium size={16} /> : <MoonStar size={16} />}
              {resolvedTheme === 'dark' ? 'Light' : 'Dark'} mode
            </button>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <section className="rounded-[32px] border border-slate-200/70 bg-white/70 p-6 shadow-glass backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-300">
                  Voice control
                </p>
                <h2 className="mt-1 text-2xl font-semibold">Command center</h2>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300">
                <span className={`h-2.5 w-2.5 rounded-full ${isListening ? 'animate-pulse bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`} />
                {isListening ? 'Listening' : 'Ready'}
              </div>
            </div>

            <div className="flex flex-col items-center gap-5 py-6">
              <button
                type="button"
                onClick={toggleListening}
                className={`group relative flex h-28 w-28 items-center justify-center rounded-full border text-white shadow-2xl transition-all duration-300 ${
                  isListening
                    ? 'border-rose-300 bg-gradient-to-br from-rose-500 via-pink-500 to-orange-400 shadow-pink-500/30'
                    : 'border-sky-300 bg-gradient-to-br from-sky-500 via-indigo-500 to-violet-500 shadow-blue-500/30'
                }`}
              >
                <span className={`absolute inset-0 rounded-full ${isListening ? 'animate-ping bg-white/20' : 'bg-white/10'}`} />
                <Mic size={38} className="relative z-10" />
              </button>

              <div className="w-full rounded-[24px] border border-slate-200/70 bg-slate-50/80 p-4 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/40">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Live transcript</p>
                <p className="mt-3 text-lg font-medium text-slate-800 dark:text-slate-100">{transcript}</p>
                <div className="mt-4 flex items-center justify-between gap-4">
                  <p className="text-sm text-slate-500 dark:text-slate-300">{statusMessage}</p>
                  <button
                    type="button"
                    onClick={() => handleVoiceSubmit()}
                    className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
                  >
                    Run command <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          </section>

          <aside className="rounded-[32px] border border-slate-200/70 bg-white/70 p-6 shadow-glass backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-300">
                  Budget
                </p>
                <h2 className="mt-1 text-2xl font-semibold">Tracker</h2>
              </div>
              <div className="rounded-full bg-amber-100 p-2 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
                <Wallet size={18} />
              </div>
            </div>

            <div className="space-y-5">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm text-slate-500 dark:text-slate-300">
                  <span>Current spend</span>
                  <span className="font-semibold text-slate-900 dark:text-white">${subtotal.toFixed(2)}</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-400"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              <div className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4 dark:border-white/10 dark:bg-slate-900/40">
                <div className="mb-3 flex items-center justify-between text-sm text-slate-500 dark:text-slate-300">
                  <span>Monthly budget</span>
                  <span>${budget.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-sm font-medium">
                  <span>Remaining</span>
                  <span className="text-emerald-600 dark:text-emerald-300">${Math.max(budget - subtotal, 0).toFixed(2)}</span>
                </div>
              </div>

              <div>
                <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-slate-500 dark:text-slate-300">
                  Filter view
                </p>
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <button
                      key={category}
                      type="button"
                      onClick={() => setActiveFilter(category)}
                      className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                        activeFilter === category
                          ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
                          : 'bg-slate-200/80 text-slate-700 dark:bg-white/5 dark:text-slate-200'
                      }`}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
          <section className="rounded-[32px] border border-slate-200/70 bg-white/70 p-6 shadow-glass backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-300">
                  Shopping list
                </p>
                <h2 className="mt-1 text-2xl font-semibold">Your cart</h2>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-sky-100 px-3 py-1.5 text-sm font-medium text-sky-700 dark:bg-sky-500/10 dark:text-sky-300">
                <ShoppingBag size={15} />
                {cartItems.length} items
              </div>
            </div>

            <div className="space-y-3">
              {visibleItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-4 rounded-[22px] border border-slate-200/70 bg-white/60 p-3.5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/30"
                >
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleToggleItem(item.id)}
                      className={`flex h-8 w-8 items-center justify-center rounded-full border transition ${
                        item.checked
                          ? 'border-emerald-500 bg-emerald-500 text-white'
                          : 'border-slate-300 bg-white text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200'
                      }`}
                    >
                      <Check size={14} />
                    </button>

                    <div>
                      <p className={`font-medium ${item.checked ? 'line-through opacity-60' : ''}`}>
                        {item.name}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-300">
                        <span className="rounded-full bg-slate-200 px-2 py-0.5 dark:bg-slate-700">{item.category}</span>
                        <span>Qty {item.quantity}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                      ${((item.price ?? 0) * item.quantity).toFixed(2)}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(item.id)}
                      className="rounded-full p-2 text-slate-500 transition hover:bg-rose-100 hover:text-rose-600 dark:text-slate-300 dark:hover:bg-rose-500/10 dark:hover:text-rose-300"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[32px] border border-slate-200/70 bg-white/70 p-6 shadow-glass backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-300">
                  Smart picks
                </p>
                <h2 className="mt-1 text-2xl font-semibold">Suggestions</h2>
              </div>
              <div className="rounded-full bg-violet-100 p-2 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300">
                <Sparkles size={18} />
              </div>
            </div>

            <div className="space-y-3">
              {suggestions.map((item, index) => (
                <div
                  key={`${item.title}-${index}`}
                  className="rounded-[22px] border border-slate-200/70 bg-white/60 p-4 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/30"
                >
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <span
                      className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${
                        item.accent === 'deal'
                          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                          : item.accent === 'substitute'
                            ? 'bg-violet-100 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300'
                            : 'bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300'
                      }`}
                    >
                      {item.accent === 'deal' ? 'Deal' : item.accent === 'substitute' ? 'Substitute' : 'Alert'}
                    </span>
                    <button type="button" className="text-slate-400 transition hover:text-slate-700 dark:hover:text-slate-200">
                      <Plus size={16} />
                    </button>
                  </div>
                  <h3 className="font-semibold text-slate-900 dark:text-white">{item.title}</h3>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.note}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
