# BharatVision Frontend

Modern React + TypeScript frontend for BharatVision Legal Metrology Compliance System.

## Features

- 🎨 Modern UI with TailwindCSS
- 📊 Interactive Dashboard with charts
- 🔍 E-Commerce Web Crawler
- 📸 OCR Image Upload & Analysis
- 📈 Analytics & Reports
- ⚡ Fast performance with Vite
- 🔒 Type-safe with TypeScript

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Router** - Routing
- **React Query** - Data fetching
- **Zustand** - State management
- **Axios** - HTTP client
- **Recharts** - Charts
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Update .env with your backend URL
# VITE_API_BASE_URL=http://localhost:8000
```

### Development

```bash
# Start dev server
npm run dev

# Open http://localhost:5173
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variable: `VITE_API_BASE_URL=https://your-backend-url.com`
4. Deploy!

### Manual Deployment

```bash
npm run build
# Deploy the 'dist' folder to your hosting provider
```

## Environment Variables

- `VITE_API_BASE_URL` - Backend API URL (required)

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   │   ├── Layout.tsx
│   │   └── ProductCard.tsx
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── WebCrawler.tsx
│   │   ├── OCRUpload.tsx
│   │   ├── Analytics.tsx
│   │   ├── Settings.tsx
│   │   └── Help.tsx
│   ├── services/       # API services
│   │   └── api.ts
│   ├── store/          # State management
│   │   └── index.ts
│   ├── types/          # TypeScript types
│   │   └── index.ts
│   ├── App.tsx         # Main app
│   ├── main.tsx        # Entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## License

Government of India - Ministry of Consumer Affairs
