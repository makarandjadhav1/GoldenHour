import jsxA11y from "eslint-plugin-jsx-a11y";
import tseslint from "typescript-eslint";

export default tseslint.config(
  ...tseslint.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      // user text is only ever rendered as text nodes
      "no-restricted-syntax": ["error", { selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']", message: "Banned: render text nodes only." }],
      // src/api.ts is the ONLY module that may touch the network (Privacy Ledger)
      "no-restricted-globals": ["error", "fetch", "XMLHttpRequest", "WebSocket", "EventSource"],
      "no-restricted-properties": ["error", { object: "navigator", property: "sendBeacon" }],
    },
  },
  { files: ["src/api.ts"], rules: { "no-restricted-globals": "off" } },
  { files: ["**/*.test.*"], rules: { "no-restricted-globals": "off" } },
);
