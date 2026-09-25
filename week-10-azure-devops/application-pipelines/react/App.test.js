import { render, screen } from '@testing-library/react';
import App from './App';

test('identifies the deployed learner and date', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /Deployed by: Eze Favour/i })).toBeInTheDocument();
  expect(screen.getByText('2026-09-25')).toBeInTheDocument();
});
