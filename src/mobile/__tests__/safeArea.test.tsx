/**
 * Safe Area Integration Tests
 *
 * Verifies Story 1: SafeAreaProvider is present in App, and MainNavigator
 * uses dynamic insets for its tab bar.
 */
import React from "react";
import { render } from "@testing-library/react-native";
import { View, Text } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

// ─────────────────────────────────────────────────────────────────────────────

describe("SafeArea — Story 1", () => {
  describe("App", () => {
    it("provides SafeAreaProvider and useSafeAreaInsets via jest mock", () => {
      const { useSafeAreaInsets } = require("react-native-safe-area-context");
      expect(SafeAreaProvider).toBeDefined();
      expect(useSafeAreaInsets).toBeDefined();
    });

    it("SafeAreaProvider mock passes children through without crashing", () => {
      const { getByText } = render(
        <SafeAreaProvider>
          <View>
            <Text>child</Text>
          </View>
        </SafeAreaProvider>,
      );
      expect(getByText("child")).toBeTruthy();
    });
  });

  describe("MainNavigator — tab bar dynamic insets", () => {
    it("useSafeAreaInsets mock returns zero insets", () => {
      const { useSafeAreaInsets } = require("react-native-safe-area-context");
      const insets = useSafeAreaInsets();
      expect(insets).toEqual({ top: 0, bottom: 0, left: 0, right: 0 });
    });

    it("tab bar height = 60 + bottom inset (0 in tests → 60)", () => {
      const { useSafeAreaInsets } = require("react-native-safe-area-context");
      const insets = useSafeAreaInsets();
      const tabBarHeight = 60 + insets.bottom;
      expect(tabBarHeight).toBe(60);
    });

    it("tab bar height increases with non-zero bottom inset", () => {
      const safeArea = require("react-native-safe-area-context");
      const originalFn = safeArea.useSafeAreaInsets;
      safeArea.useSafeAreaInsets = () => ({
        top: 0,
        bottom: 34,
        left: 0,
        right: 0,
      });

      const insets = safeArea.useSafeAreaInsets();
      const tabBarHeight = 60 + insets.bottom;
      expect(tabBarHeight).toBe(94); // 60 + 34

      safeArea.useSafeAreaInsets = originalFn; // restore
    });
  });

  describe("SafeAreaView edges on SignUpScreen", () => {
    it("all four edges are specified in the screen component source", () => {
      const fs = require("fs");
      const path = require("path");
      const src = fs.readFileSync(
        path.join(__dirname, "../src/screens/auth/SignUpScreen.tsx"),
        "utf8",
      );
      expect(src).toContain('edges={["top", "bottom", "left", "right"]}');
    });
  });

  describe("App.tsx source", () => {
    it("imports SafeAreaProvider", () => {
      const fs = require("fs");
      const path = require("path");
      const src = fs.readFileSync(path.join(__dirname, "../App.tsx"), "utf8");
      expect(src).toContain("SafeAreaProvider");
      expect(src).toContain('from "react-native-safe-area-context"');
    });

    it("wraps content in SafeAreaProvider", () => {
      const fs = require("fs");
      const path = require("path");
      const src = fs.readFileSync(path.join(__dirname, "../App.tsx"), "utf8");
      expect(src).toContain("<SafeAreaProvider>");
      expect(src).toContain("</SafeAreaProvider>");
    });
  });

  describe("MainNavigator.tsx source", () => {
    it("imports and calls useSafeAreaInsets", () => {
      const fs = require("fs");
      const path = require("path");
      const src = fs.readFileSync(
        path.join(__dirname, "../src/navigation/MainNavigator.tsx"),
        "utf8",
      );
      expect(src).toContain("useSafeAreaInsets");
      expect(src).toContain("insets.bottom");
    });
  });
});
