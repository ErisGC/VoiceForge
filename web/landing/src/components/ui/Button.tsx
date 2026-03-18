"use client";

import { type ButtonHTMLAttributes, forwardRef } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  href?: string;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-primary-500 to-accent-violet text-white shadow-[0_0_24px_rgba(109,124,255,0.3)] hover:shadow-[0_0_32px_rgba(109,124,255,0.45)] hover:brightness-110",
  secondary:
    "bg-surface-800 border border-border-strong text-text-100 hover:border-primary-400 hover:bg-surface-700",
  ghost:
    "bg-transparent text-text-300 hover:text-text-100 hover:bg-white/5",
};

const sizeClasses: Record<ButtonSize, string> = {
  md: "px-6 py-3 text-sm",
  lg: "px-8 py-4 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    { variant = "primary", size = "md", className = "", children, href, ...props },
    ref,
  ) {
    const classes = [
      "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-200 cursor-pointer",
      "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-400",
      "disabled:opacity-40 disabled:cursor-not-allowed",
      variantClasses[variant],
      sizeClasses[size],
      className,
    ].join(" ");

    if (href) {
      return (
        <a href={href} className={classes} role="button">
          {children}
        </a>
      );
    }

    return (
      <button ref={ref} className={classes} {...props}>
        {children}
      </button>
    );
  },
);
