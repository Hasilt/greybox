// Display formatters. Every one tolerates null/undefined and returns an em dash.

const DASH = '—';

export const int = (v) =>
  v == null || Number.isNaN(v) ? DASH : Math.round(v).toLocaleString('en-US');

export const pct = (v, digits = 1) =>
  v == null || Number.isNaN(v) ? DASH : `${(v * 100).toFixed(digits)}%`;

export const ms = (v) => (v == null || Number.isNaN(v) ? DASH : Math.round(v).toLocaleString('en-US'));

export const decimal = (v, digits = 3) =>
  v == null || Number.isNaN(v) ? DASH : Number(v).toFixed(digits);

export const clockTime = (epochMs) =>
  new Date(epochMs).toLocaleTimeString('en-US', { hour12: false });

export const clockDateTime = (epochMs) =>
  new Date(epochMs).toLocaleString('en-US', { hour12: false });
