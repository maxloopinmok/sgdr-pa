// Device-aware default-view thresholds for the calendar pages.
// Tunable after live testing — see spec section 2.5.3.
window.SGDR_BREAKPOINTS = {
  // Phone breakpoint (px). Below this width, use the device-aware default view.
  PHONE_MAX_WIDTH: 768,
  // If today's event count exceeds this on phone, open in single-day view;
  // otherwise open in current-week view.
  PHONE_DAY_DENSITY_THRESHOLD: 4,
};
