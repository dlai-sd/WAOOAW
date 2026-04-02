import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';

jest.mock('@react-native-picker/picker', () => {
  const ReactLib = require('react');

  const Picker = ({ children, ...props }: any) =>
    ReactLib.createElement('Picker', props, children);
  Picker.Item = ({ label, value }: any) =>
    ReactLib.createElement('PickerItem', { label, value });

  return { Picker };
});

jest.mock('../../../hooks/useTheme', () => ({
  useTheme: () => ({
    colors: {
      black: '#0a0a0a',
      white: '#ffffff',
      gray400: '#a1a1aa',
    },
    spacing: {
      md: 16,
      lg: 24,
    },
    typography: {
      textVariants: {
        body: {},
      },
    },
  }),
}));

import FilterAgentsScreen from '../FilterAgentsScreen';

describe('FilterAgentsScreen', () => {
  it('renders an Apply Filters button', () => {
    render(
      <FilterAgentsScreen
        navigation={{ navigate: jest.fn() } as any}
        route={{ key: 'filter', name: 'FilterAgents', params: {} } as any}
      />
    );

    expect(screen.getByText('Apply Filters')).toBeTruthy();
  });

  it('navigates back to Discover with selected filters', () => {
    const navigate = jest.fn();
    const rendered = render(
      <FilterAgentsScreen
        navigation={{ navigate } as any}
        route={{
          key: 'filter',
          name: 'FilterAgents',
          params: { industry: 'Marketing', minRating: 2, maxPrice: 12000 },
        } as any}
      />
    );

    rendered.UNSAFE_getByType('Picker').props.onValueChange('Sales');

    const inputs = screen.getAllByDisplayValue(/^(2|12000)$/);
    fireEvent.changeText(inputs[0], '4');
    fireEvent.changeText(inputs[1], '15000');
    fireEvent.press(screen.getByText('Apply Filters'));

    expect(navigate).toHaveBeenCalledWith('Discover', {
      industry: 'sales',
      minRating: 4,
      maxPrice: 15000,
    });
  });
});
