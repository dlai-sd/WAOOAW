/**
 * Mock for expo-image
 * Provides a lightweight Image component for testing
 */
const React = require("react");

const Image = React.forwardRef((props, ref) =>
  React.createElement("Image", { ...props, ref }),
);
Image.displayName = "ExpoImage";

module.exports = {
  Image,
};
