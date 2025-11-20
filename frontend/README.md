# MoveHub Frontend

Production-grade frontend for MoveHub moving services marketplace built with Next.js 14, TypeScript, and Tailwind CSS.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Strict type safety throughout
- **Tailwind CSS** - Utility-first CSS framework
- **React Hook Form** - Type-safe form management
- **Zod** - Runtime schema validation
- **TanStack Query** - Data fetching and caching
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install
# or
bun install

# Copy environment variables
cp .env.example .env

# Run development server
npm run dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── book/              # Booking workflow
│   ├── booking/[id]/      # Booking details
│   └── page.tsx           # Homepage
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   └── booking/          # Booking-specific components
├── lib/                  # Utilities and helpers
│   ├── api/             # API client and services
│   ├── validations/     # Zod schemas
│   ├── utils.ts         # Helper functions
│   └── constants.ts     # App constants
└── types/               # TypeScript type definitions
```

## Features

### Customer Booking Workflow ✓

- **Multi-step form** with validation
- **Real-time validation** with Zod schemas
- **Type-safe** API calls
- **Responsive design** for mobile/desktop
- **Progress indicator** for better UX
- **Price estimation** with detailed breakdown
- **No account required** - just email and phone

### Booking Management

- View booking details
- Track booking status
- See assigned driver and truck information
- Print confirmation

## Type Safety

All data is strongly typed:

- **Backend schemas** mirrored as TypeScript types
- **Runtime validation** with Zod
- **Form validation** with React Hook Form + Zod
- **API responses** validated at runtime

## Development

```bash
# Run type checking
npm run type-check

# Run linter
npm run lint

# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Workflows Implemented

1. **Customer Booking** ✓
   - Multi-step form (Contact → Pickup → Dropoff → Details → Review)
   - Real-time validation
   - Price estimation
   - Booking confirmation

2. **Booking Status** (Planned)
   - Track booking by ID or email
   - Real-time status updates
   - Driver location tracking

3. **Mover Signup** (Planned)
   - Company registration
   - Document upload
   - Verification workflow

## Code Quality

- **ESLint** - Code linting
- **TypeScript strict mode** - Maximum type safety
- **Component-driven** - Reusable UI components
- **Clean code** - Readable and maintainable

## License

Proprietary
