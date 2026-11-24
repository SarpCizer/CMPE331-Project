import Icon from "./Icon";

// Wordmark. `small` is the compact footer version; `className` adds
// screen-specific sizing.
export default function Brand({ small = false, className = "" }) {
  return (
    <div
      className={`flex items-center font-[750] tracking-[-0.065em] leading-none ${
        small ? "text-[1.15rem]" : "text-[1.75rem]"
      } ${className}`}
    >
      <span
        className={`mr-[9px] flex bg-green text-white ${
          small ? "rounded-[7px] p-1" : "rounded-[11px] p-[7px]"
        }`}
      >
        <Icon className={small ? "h-[15px] w-[15px]" : "h-[22px] w-[22px]"} />
      </span>
      fridgely<span className="text-[#c7774f]">.</span>
    </div>
  );
}
