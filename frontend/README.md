# Frontend — Noviq Intelligence

### AI Resume Fraud Detection System

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 + Framer Motion + Recharts.

## Running locally

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL if the backend isn't on :8000
npm run dev
```

Requires the backend API running (see `../backend/README.md`).

## Layout

```
app/
├── layout.tsx                 root layout: fonts, theme init script, providers
├── page.tsx                   redirects to /dashboard or /login based on auth state
├── (auth)/                    login + register, centered auth layout
└── (dashboard)/               protected route group (redirects to /login if signed out)
    ├── layout.tsx              sidebar + topbar + mobile nav shell
    ├── dashboard/              recruiter analytics dashboard (stat tiles + charts)
    ├── candidates/             candidate list, candidate detail + resume upload
    │   └── [id]/resumes/[resumeId]/   fraud analysis detail + PDF report download
    ├── upload/                 standalone "pick or create candidate, then upload" flow
    └── admin/                  user management (admin role only)

components/
├── ui/                        Button, Card, Badge, Input, Modal, Spinner, EmptyState, ErrorBanner
├── layout/                    Sidebar, Topbar, MobileNav
├── charts/                    Recharts wrappers (risk distribution, fraud trend, flag categories)
├── analysis/                  RiskMeter, ScoreBreakdown, FraudFlagCard
├── candidates/                AddApplicantForm, ResumeUploadCard, ResumeRow
├── theme-provider.tsx          class-based dark/light mode (persisted, system-default on first load)
└── ThemeToggle.tsx

lib/
├── api.ts                     typed fetch client (JWT auth, auto refresh-on-401)
├── auth-context.tsx            React context wrapping api.ts auth calls + token state
├── types.ts                    TypeScript mirrors of the backend Pydantic schemas
├── hooks.ts                    useAsync — small data-fetching hook used by every page
└── utils.ts                    cn(), formatters, risk/category color-token helpers
```

## Auth model

JWT access + refresh tokens are stored in `localStorage` (`lib/api.ts::tokenStorage`).
Because the token lives client-side, every route under `(dashboard)` is a Client
Component that checks `useAuth().isAuthenticated` in `app/(dashboard)/layout.tsx` and
redirects to `/login` if signed out — there's no server-side session to check during
SSR, so this guard is intentionally client-side.

## Design system

Colors are CSS custom properties in `app/globals.css`, themed via a `.dark` class
toggle (Tailwind v4 `@custom-variant dark`). The risk/status colors (low/medium/high)
and chart categorical palette come from a colorblind-safe validated reference palette —
see the `dataviz` skill if you're adding a new chart or changing a color.
