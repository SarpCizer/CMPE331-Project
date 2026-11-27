export const recipeMoods = [
  {
    id: "lazy",
    label: "I'm Lazy",
    emoji: "😴",
    hint: "Little effort. Up to 15 min.",
  },
  {
    id: "high-protein",
    label: "High Protein",
    emoji: "💪",
    hint: "Something satisfying.",
  },
  {
    id: "sweet",
    label: "Sweet Cravings",
    emoji: "🍫",
    hint: "A little sweet moment.",
  },
  {
    id: "quick",
    label: "Quick & Easy",
    emoji: "⏱️",
    hint: "Good food. Up to 20 min.",
  },
  { id: "healthy", label: "Healthy", emoji: "🥗", hint: "A balanced plate." },
];

export default function RecipeMoodPicker({ value, onChange, disabled }) {
  return (
    <fieldset className="m-0 my-6 min-w-0 border-0 p-0" disabled={disabled}>
      <legend className="mb-2 p-0 font-serif text-[1.5rem] font-semibold tracking-[-0.03em]">
        What's your mood?
      </legend>
      <p className="mb-4 text-[0.9rem]">
        A craving, a busy day, a little comfort. Find a recipe that fits.
      </p>
      <div className="grid grid-cols-3 gap-3 mobile:grid-cols-2">
        {recipeMoods.map((mood) => {
          const selected = value === mood.id;
          return (
            <button
              key={mood.id}
              type="button"
              aria-pressed={selected}
              onClick={() => onChange(selected ? null : mood.id)}
              className={`flex min-h-[136px] min-w-0 flex-col items-center justify-center gap-2 rounded-[15px] border px-3 py-4 text-center ${selected ? "border-green bg-green text-white" : "border-[#ccd8c8] bg-[#f8faf5] text-green hover:bg-[#e5eddf]"}`}
            >
              <span aria-hidden="true" className="text-[1.8rem] leading-none">
                {mood.emoji}
              </span>
              <span className="text-[0.95rem] font-semibold">{mood.label}</span>
              <span
                className={`text-[0.75rem] leading-[1.4] ${selected ? "text-[#edf3e9]" : "text-[#56685a]"}`}
              >
                {mood.hint}
              </span>
            </button>
          );
        })}
      </div>
      <div className="mt-3 flex min-h-[28px] flex-wrap items-center justify-between gap-2 text-[0.8rem]">
        <span className="text-muted">
          Your saved dietary preferences and exclusions still apply.
        </span>
        {value && (
          <button
            type="button"
            className="btn-text"
            onClick={() => onChange(null)}
          >
            Clear mood
          </button>
        )}
      </div>
    </fieldset>
  );
}
