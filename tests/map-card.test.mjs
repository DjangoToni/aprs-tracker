import assert from "node:assert/strict";

globalThis.HTMLElement = class {};
globalThis.customElements = { get: () => true, define: () => {} };
globalThis.window = { customCards: [] };

const { historyPoints, markerStatus, validCoordinate } = await import(
  "../custom_components/aprs_monitor/frontend/aprs-monitor-map-card.js"
);

assert.equal(validCoordinate(47.3769, 8.5417), true);
assert.equal(validCoordinate(91, 8.5417), false);
assert.equal(validCoordinate(47.3769, null), false);

assert.equal(markerStatus({ state: "home", attributes: {} }), "current");
assert.equal(
  markerStatus({ state: "not_home", attributes: { position_stale: true } }),
  "stale",
);
assert.equal(markerStatus({ state: "unavailable", attributes: {} }), "unavailable");
assert.equal(markerStatus({ state: "home", attributes: {} }, true), "unavailable");

const points = historyPoints(
  [
    { attributes: { latitude: 47.1, longitude: 8.1 } },
    { attributes: { latitude: 47.1, longitude: 8.1 } },
    { a: { latitude: 47.2, longitude: 8.2 } },
    { a: { latitude: 999, longitude: 8.3 } },
    { attributes: { latitude: 47.3, longitude: 8.3 } },
  ],
  100,
);
assert.deepEqual(points, [
  [47.1, 8.1],
  [47.2, 8.2],
  [47.3, 8.3],
]);

const longTrack = Array.from({ length: 10 }, (_, index) => ({
  a: { latitude: 47 + index / 100, longitude: 8 + index / 100 },
}));
const sampled = historyPoints(longTrack, 4);
assert.equal(sampled.length, 4);
assert.deepEqual(sampled[0], [47, 8]);
assert.deepEqual(sampled.at(-1), [47.09, 8.09]);

console.log("APRS Monitor map-card tests passed");
