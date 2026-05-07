interface ProgressBarProps {
  value: number; // 0..1
}

export function ProgressBar({ value }: ProgressBarProps) {
  return (
    <div className="qprog-bar">
      <div
        className="qprog-fill"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}
