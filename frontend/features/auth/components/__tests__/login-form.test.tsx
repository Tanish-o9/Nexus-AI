import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LoginForm } from '../login-form';

// Mock Next.js Link
vi.mock('next/link', () => {
  return {
    default: ({ children, href }: { children: React.ReactNode; href: string }) => (
      <a href={href}>{children}</a>
    ),
  };
});

// Mock hook dependency
const mockMutate = vi.fn();
vi.mock('@/features/auth/hooks/use-login', () => ({
  useLogin: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

describe('LoginForm Component', () => {
  it('renders email and password inputs and submit button', () => {
    render(<LoginForm />);
    
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument();
  });

  it('submits form with user input', () => {
    render(<LoginForm />);
    
    const emailInput = screen.getByLabelText(/Email/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitButton = screen.getByRole('button', { name: /Sign in/i });

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    expect(mockMutate).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123',
    });
  });
});
