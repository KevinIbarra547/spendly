#!/bin/bash

# Spendly Project Setup Script
# This script initializes the project with all necessary dependencies and configuration

set -e  # Exit on error

echo "🚀 Setting up Spendly project..."
echo ""

# Check if we're in the right directory
if [ ! -f "SPEC.md" ]; then
    echo "❌ Error: Please run this script from the Spendly repository root"
    exit 1
fi

# Step 1: Initialize package.json if it doesn't exist
if [ ! -f "package.json" ]; then
    echo "📦 Initializing package.json..."
    cp package.template.json package.json
    echo "✅ package.json created"
else
    echo "✅ package.json already exists"
fi

# Step 2: Install npm dependencies
if [ ! -d "node_modules" ]; then
    echo "📥 Installing npm dependencies..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Step 3: Set up husky for git hooks
if [ ! -d ".git/hooks" ] || [ ! -f ".git/hooks/pre-commit" ]; then
    echo "🔧 Setting up Git hooks with husky..."
    npm run prepare
    echo "✅ Git hooks configured"
else
    echo "✅ Git hooks already configured"
fi

# Step 4: Create initial folder structure
for dir in src/backend src/frontend src/shared/contracts src/shared/types src/shared/tests tests/unit tests/integration tests/contracts tests/regression tests/mocks; do
    if [ ! -d "$dir" ]; then
        echo "📁 Creating directory: $dir"
        mkdir -p "$dir"
    fi
done

echo "✅ Directory structure created"

# Step 5: Create placeholder files
if [ ! -f "src/backend/index.ts" ]; then
    echo "📄 Creating backend entry point..."
    cat > src/backend/index.ts << 'EOF'
// Spendly Backend Entry Point
// This will be implemented in Phase 1

import express from 'express';

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Spendly backend running on port ${PORT}`);
});
EOF
    echo "✅ Backend entry point created"
fi

if [ ! -f "src/frontend/main.tsx" ]; then
    echo "📄 Creating frontend entry point..."
    cat > src/frontend/main.tsx << 'EOF'
// Spendly Frontend Entry Point
// This will be implemented in Phase 3

import React from 'react';
import ReactDOM from 'react-dom/client';

const App = () => {
  return (
    <div>
      <h1>Spendly</h1>
      <p>A money-life simulation web app</p>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
EOF
    echo "✅ Frontend entry point created"
fi

# Step 6: Create TypeScript configuration
if [ ! -f "tsconfig.json" ]; then
    echo "📄 Creating TypeScript configuration..."
    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "allowSyntheticDefaultImports": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@backend/*": ["src/backend/*"],
      "@frontend/*": ["src/frontend/*"],
      "@shared/*": ["src/shared/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
EOF
    echo "✅ TypeScript configuration created"
fi

# Step 7: Create ESLint configuration
if [ ! -f ".eslintrc.json" ]; then
    echo "📄 Creating ESLint configuration..."
    cat > .eslintrc.json << 'EOF'
{
  "env": {
    "browser": true,
    "es2021": true,
    "node": true,
    "jest": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:prettier/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module",
    "project": ["./tsconfig.json"]
  },
  "plugins": ["@typescript-eslint", "prettier"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "prettier/prettier": "error",
    "no-console": "warn",
    "prefer-const": "error",
    "no-var": "error"
  },
  "ignorePatterns": ["dist", "node_modules", "*.js"]
}
EOF
    echo "✅ ESLint configuration created"
fi

# Step 8: Create Prettier configuration
if [ ! -f ".prettierrc" ]; then
    echo "📄 Creating Prettier configuration..."
    cat > .prettierrc << 'EOF'
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
EOF
    echo "✅ Prettier configuration created"
fi

# Step 9: Create Jest configuration
if [ ! -f "jest.config.js" ]; then
    echo "📄 Creating Jest configuration..."
    cat > jest.config.js << 'EOF'
/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@backend/(.*)$': '<rootDir>/src/backend/$1',
    '^@frontend/(.*)$': '<rootDir>/src/frontend/$1',
    '^@shared/(.*)$': '<rootDir>/src/shared/$1'
  },
  collectCoverageFrom: ['src/**/*.ts', '!src/**/*.d.ts'],
  coverageDirectory: 'coverage',
  verbose: true
};
EOF
    echo "✅ Jest configuration created"
fi

# Step 10: Create lint-staged configuration
if [ ! -f ".lintstagedrc" ]; then
    echo "📄 Creating lint-staged configuration..."
    cat > .lintstagedrc << 'EOF'
{
  "*.{ts,tsx}": [
    "npm run lint:no-fix",
    "npm run typecheck",
    "git add"
  ]
}
EOF
    echo "✅ lint-staged configuration created"
fi

# Step 11: Verify setup
echo ""
echo "🔍 Verifying setup..."

# Check if all essential files exist
ESSENTIAL_FILES=(
  "package.json"
  "tsconfig.json"
  ".eslintrc.json"
  ".prettierrc"
  "jest.config.js"
  ".lintstagedrc"
  "src/backend/index.ts"
  "src/frontend/main.tsx"
  ".github/CODEOWNERS"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/workflows/ci.yml"
)

ALL_EXIST=true
for file in "${ESSENTIAL_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing: $file"
    ALL_EXIST=false
  fi
done

if [ "$ALL_EXIST" = true ]; then
    echo "✅ All essential files are in place"
else
    echo "⚠️  Some files are missing"
fi

echo ""
echo "🎉 Spendly project setup complete!"
echo ""
echo "Next steps:"
echo "1. Replace GitHub usernames in .github/CODEOWNERS"
echo "2. Run 'npm run dev' to start development"
echo "3. Configure branch protection in GitHub settings"
echo "4. Start Phase 0: Foundation"
echo ""
