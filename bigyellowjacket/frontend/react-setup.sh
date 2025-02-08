# Create and navigate to project directory
New-Item -ItemType Directory -Path "bigyellowjacket-ui"
cd bigyellowjacket-ui

# Initialize Vite project
npm create vite@latest . -- --template react-ts

# Install base dependencies (when prompted, press 'y' and Enter)
npm install

# Install required packages
npm install @radix-ui/react-tabs
npm install recharts
npm install lucide-react
npm install @tanstack/react-query
npm install tailwindcss
npm install postcss
npm install autoprefixer
npm install zustand
npm install clsx
npm install date-fns
npm install class-variance-authority
npm install tailwind-merge
npm install @radix-ui/react-tabs recharts lucide-react @tanstack/react-query tailwindcss postcss autoprefixer zustand clsx date-fns class-variance-authority tailwind-merge
# Initialize Tailwind
npx tailwindcss init -p

# Start the development server
npm run dev

