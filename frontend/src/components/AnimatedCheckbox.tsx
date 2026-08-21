import { motion } from "framer-motion";

export default function AnimatedCheckbox({ checked, onToggle }: { checked: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      className={`check-box${checked ? " checked" : ""}`}
      onClick={onToggle}
    >
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
        <motion.path
          d="M3 8.5L6.5 12L13 4.5"
          stroke="#fff"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={false}
          animate={{ pathLength: checked ? 1 : 0, opacity: checked ? 1 : 0 }}
          transition={{ duration: 0.28, ease: "easeOut" }}
        />
      </svg>
    </button>
  );
}
