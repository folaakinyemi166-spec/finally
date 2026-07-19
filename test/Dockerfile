# Playwright test runner image — kept separate from the production Dockerfile
# at the project root so browser binaries never end up in the shipped image
# (PLAN.md §12). The image tag version must match @playwright/test's version
# in package.json exactly (browser binaries are bundled per-version).
FROM mcr.microsoft.com/playwright:v1.61.1-noble

WORKDIR /tests
COPY package.json ./
RUN npm install
COPY . .

CMD ["npx", "playwright", "test"]
