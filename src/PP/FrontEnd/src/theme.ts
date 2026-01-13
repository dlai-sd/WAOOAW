import { createLightTheme, createDarkTheme, BrandVariants, Theme } from '@fluentui/react-components'

const waooawBrandColors: BrandVariants = {
  10: '#f5f9ff',
  20: '#e6f2ff',
  30: '#c2e0ff',
  40: '#9dceff',
  50: '#78bcff',
  60: '#4da6ff',
  70: '#2490ff',
  80: '#0078d4',
  90: '#0066b8',
  100: '#00529c',
  110: '#004080',
  120: '#003366',
  130: '#00254d',
  140: '#001933',
  150: '#000d1a',
  160: '#000000'
}

export const waooawLightTheme: Theme = createLightTheme(waooawBrandColors)
export const waooawDarkTheme: Theme = createDarkTheme(waooawBrandColors)
