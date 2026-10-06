import { FlatCompat } from "@eslint/eslintrc";
const compat = new FlatCompat({ baseDirectory: import.meta.dirname });
const config = [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts", "demo-dist/**"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // Spec §4 / R6: vendor- and request-derived text is rendered as plain text only.
    rules: {
      "react/no-danger": "error",
      "no-restricted-syntax": ["error",
        { selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']", message: "Never render untrusted content as HTML." },
        { selector: "Identifier[name='dangerouslySetInnerHTML']", message: "Never render untrusted content as HTML." },
        { selector: "Property[key.name='innerHTML']", message: "No innerHTML." },
      ],
      "@next/next/no-img-element": "error",
    },
  },
];
export default config;
