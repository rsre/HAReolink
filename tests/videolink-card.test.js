const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

global.HTMLElement = class {
  attachShadow() {
    this.shadowRoot = {};
  }
};
global.customElements = { get: () => undefined, define: () => undefined };
global.window = { customCards: [] };

const source = fs.readFileSync(
  "custom_components/videolink_doorbell/frontend/videolink-doorbell.js",
  "utf8",
);
vm.runInThisContext(`${source}\nglobal.CardUnderTest = VideolinkDoorbellCard;`);

test("new cards default to scaled video", () => {
  assert.equal(CardUnderTest.getStubConfig(undefined, ["camera.front_door"]).video_fit, "contain");
});

test("the editor exposes the supported video modes", () => {
  const field = CardUnderTest.getConfigForm().schema.find(({ name }) => name === "video_fit");
  assert.equal(field.selector.select.mode, "dropdown");
  assert.deepEqual(field.selector.select.options.map(({ value }) => value), [
    "cover", "contain", "fill", "full",
  ]);
});

test("hide_video selects compact audio-only behavior", () => {
  const card = new CardUnderTest();
  card._render = () => undefined;
  card.setConfig({ entity: "camera.front_door", hide_video: true });
  assert.equal(card._audioOnly, true);
  assert.equal(card.getCardSize(), 2);
});
