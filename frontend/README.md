# Frontend

This folder holds the chat UI of the plugin: the floating button and the chat panel shown on every Jenkins page. It's a React app written in TypeScript, built with [Vite](https://vite.dev/) and styled with [Material UI](https://mui.com/).

Inside Jenkins, the UI doesn't call the backend directly. Every request goes through the Jenkins Controller (`/chatbot-api/`), as the [architecture overview](https://jenkinsci.github.io/user-guide-ai-chatbot-plugin/developer-docs/api/index.html) explains. During local development, the UI calls the backend directly instead (see [`src/api/api.ts`](src/api/api.ts)).

## Local development

Prerequisites: _Node.js_ (`^20.19.0 || ^22.13.0 || >=24`) and a backend running on `http://localhost:8000` (see the [Development Guide](https://jenkinsci.github.io/user-guide-ai-chatbot-plugin/developer-docs/developing.html)).

The backend only accepts requests that carry a JWT signed with its `JWT_SECRET_KEY`. The command below requires [uv](https://docs.astral.sh/uv/getting-started/installation/); install it first if it is not already available. To generate a token for development, run this from the repository root:

```shell
cd backend
uv run python -c "import os; from dotenv import load_dotenv; from jose import jwt; load_dotenv(); print(jwt.encode({'sub': 'dev-user'}, os.environ['JWT_SECRET_KEY'], algorithm='HS256'))"
```

Create `frontend/.env.local` with the token (the file is git-ignored):

```shell
VITE_DEV_API_URL=http://localhost:8000/
VITE_DUMMY_JWT_KEY=<token>
```

The trailing slash in `VITE_DEV_API_URL` is required because the app appends request paths such as `chats` directly to it.

Install the dependencies and then start the development server:

```shell
cd ../frontend
npm install
npm run dev
```

Then open <http://localhost:5173/plugin/user-guide-ai-chatbot/>. The `/plugin/user-guide-ai-chatbot/` part is the `base` path set in [`vite.config.ts`](vite.config.ts).

## Scripts

- `npm run dev`: start the development server
- `npm run build`: type-check and build the bundle
- `npm run lint`: run ESLint
- `npm run preview`: serve the production build (API calls only work inside Jenkins)

## Build

`npm run build` writes `js/bundle.js` and `css/index.css` to `src/main/webapp`, the folder the plugin serves its static files from. It's git-ignored and emptied on every build.

You don't need to run it yourself when working on the whole plugin: `mvn clean hpi:run` runs `npm install` and `npm run build` for you through the `frontend-maven-plugin` configured in the root [`pom.xml`](../pom.xml).

## Contributing

Refer to our [contribution guidelines](https://github.com/jenkinsci/.github/blob/master/CONTRIBUTING.md).