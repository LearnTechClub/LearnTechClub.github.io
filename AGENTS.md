# Project setup

- This is a static, single-page site. `index.html` contains the markup and inline CSS; there is no JavaScript, framework, package manager, build step, or test suite.
- Edit `index.html` directly. Do not search for Node.js tooling or install dependencies for routine changes.
- The background image is referenced at `../assets/enlight.jpg`, in a separate sibling `assets` repository. For local previews, serve the parent directory so that this relative path resolves.
- `.github/workflows/pages.yaml` uploads the repository as-is to GitHub Pages. Pull requests upload an artifact; pushes to `main` also deploy it. `CNAME` sets the custom domain to `LearnTech.Club`.
- Validate edits with `git diff --check`; for visual changes, inspect the page in a browser at relevant viewport sizes. No build command is needed.
