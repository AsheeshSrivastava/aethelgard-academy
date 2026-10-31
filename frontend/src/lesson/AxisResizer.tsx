import { useRef, type KeyboardEvent, type PointerEvent, type RefObject } from "react";

import { AXIS_WIDTH_STEP, clampAxisWidth, DEFAULT_AXIS_WIDTH, MAX_AXIS_SHARE, MIN_AXIS_WIDTH, saveAxisWidth } from "./axisWidth";

/** The handle between the lesson and AXIS: drag it, or use the arrow keys. */
export function AxisResizer({
  layout,
  width,
  onChange,
}: {
  layout: RefObject<HTMLDivElement | null>;
  width: number;
  onChange: (width: number) => void;
}) {
  const dragging = useRef(false);

  function apply(next: number, save: boolean) {
    const clamped = clampAxisWidth(next, layout.current?.clientWidth || Number.MAX_SAFE_INTEGER);
    onChange(clamped);
    if (save) saveAxisWidth(clamped);
  }

  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    dragging.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
    document.body.classList.add("resizing");
  }

  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    const box = layout.current?.getBoundingClientRect();
    if (dragging.current && box) apply(box.right - event.clientX, false);
  }

  function onPointerEnd() {
    if (!dragging.current) return;
    dragging.current = false;
    document.body.classList.remove("resizing");
    saveAxisWidth(width);
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowLeft") apply(width + AXIS_WIDTH_STEP, true);
    else if (event.key === "ArrowRight") apply(width - AXIS_WIDTH_STEP, true);
    else return;
    event.preventDefault();
  }

  return (
    <div
      className="axis-resizer"
      role="separator"
      aria-label="Resize AXIS panel"
      aria-orientation="vertical"
      aria-valuenow={width}
      aria-valuemin={MIN_AXIS_WIDTH}
      aria-valuemax={Math.round((layout.current?.clientWidth || window.innerWidth) * MAX_AXIS_SHARE)}
      tabIndex={0}
      title="Drag to resize. Double-click to reset."
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerEnd}
      onPointerCancel={onPointerEnd}
      onDoubleClick={() => apply(DEFAULT_AXIS_WIDTH, true)}
      onKeyDown={onKeyDown}
    />
  );
}
