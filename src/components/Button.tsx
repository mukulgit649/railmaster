import React from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'success'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-rail-blue text-white border-rail-blue hover:bg-rail-blueDark',
  secondary: 'bg-white text-gray-800 border-rail-border hover:bg-gray-50',
  danger: 'bg-white text-rail-red border-rail-red hover:bg-red-50',
  success: 'bg-rail-green text-white border-rail-green hover:bg-green-700',
}

export default function Button({ variant = 'secondary', className = '', children, ...rest }: ButtonProps) {
  return (
    <button
      className={`px-3 py-1.5 text-sm font-medium border disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-100 ${variantClasses[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  )
}
