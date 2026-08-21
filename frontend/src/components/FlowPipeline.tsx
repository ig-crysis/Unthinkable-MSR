import { motion, useReducedMotion } from "framer-motion";
import type { MeetingStatus } from "../types";
import { STAGES, getStageIndex } from "../utils/pipeline";

export default function FlowPipeline({ status }: { status: MeetingStatus }) {
  const currentIndex = getStageIndex(status);
  const isComplete = status === "completed";
  const fillPercent = (currentIndex / (STAGES.length - 1)) * 100;
  const reduceMotion = useReducedMotion();

  return (
    <div className="flow-pipeline" aria-label="Processing pipeline">
      <div className="flow-track">
        <motion.div
          className="flow-track-fill"
          initial={false}
          animate={{ width: `${fillPercent}%` }}
          transition={{ duration: reduceMotion ? 0 : 0.6, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      {STAGES.map((stage, i) => {
        const state = i < currentIndex || (i === currentIndex && isComplete) ? "done" : i === currentIndex ? "current" : "upcoming";
        return (
          <div className={`flow-stage ${state}`} key={stage.key}>
            <motion.div
              className={`flow-node ${state}`}
              initial={false}
              animate={
                reduceMotion
                  ? undefined
                  : state === "current"
                    ? { scale: [1, 1.15, 1] }
                    : { scale: 1 }
              }
              transition={{ duration: 0.45, ease: "easeOut" }}
            >
              {state === "current" && <span className="flow-pulse" />}
              {state === "done" ? (
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <motion.path
                    d="M3 8.5L6.5 12L13 4.5"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                  />
                </svg>
              ) : (
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{i + 1}</span>
              )}
            </motion.div>
            <span className="flow-label">{stage.label}</span>
          </div>
        );
      })}
    </div>
  );
}
