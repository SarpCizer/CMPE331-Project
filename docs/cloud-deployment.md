# Cloud deployment

The deployable unit is one Docker web service containing the built React app, self-hosted Swagger UI and FastAPI host, connected to managed PostgreSQL 17. HTTPS terminates at Render. Frontend requests use `/api` on the same origin. Data never depends on the container's ephemeral filesystem.

`render.yaml` declares free resources in Frankfurt, a database reference for `DATABASE_URL`, a platform-generated `JWT_SECRET`, and readiness checks at `/api/health`. It deploys **feature/berfin-cloud-candidate**, which contains the final relational migration, integrated tests and evidence, with subsequent deploys gated on successful GitHub checks. The repository defaults to the one containing the Blueprint, supporting either the primary private source or an authorized private fork. No merge to main is required or performed. The initial Blueprint sync is reviewed separately in Render. The existing `fridgely-postgres` instance should be adopted rather than duplicated.

The Docker build pins Node 24 / pnpm 11.25.0, frontend dependencies and Python runtime dependencies. The runtime runs as a non-root user. The start script explicitly applies the Alembic migration and then starts a single Uvicorn worker bound to `0.0.0.0:$PORT`. Importing the app does not run migrations. Concurrent Argon2 work is bounded to avoid unbounded password-hashing memory on the teaching instance. Database migrations are packaged in the installed wheel and apply successfully even when the source checkout is absent.

## Configure and deploy

1. Grant Render's GitHub integration access to the private `SarpCizer/CMPE331-Project` repository if Render requests it.
2. Import the pushed `render.yaml` from `feature/berfin-cloud-candidate`, inspect the plan, adopt the existing database and apply the free web service plan. For an authorized private fork, copy this branch too, grant the Render app access to that repository and enable its GitHub Actions checks. Do not make the code public to bypass access.
3. Add the team's valid `OPENAI_API_KEY` directly under the web service's **Environment** settings and save/deploy. Do not put a key in GitHub source, frontend variables or the test report. The optional `OPENAI_MODEL` setting defaults to the provider module's model.
4. Monitor the deploy until **live**, then verify `/`, `/api/health`, `/api/openapi.json`, and `/api/docs`. Register two accounts, verify data isolation and reload persistence, then redeploy and verify stored data and authentication remain valid. Run a live recipe scenario once the provider key is configured.

Render's free service sleeps after 15 minutes without traffic and can take about a minute to wake. The free database expires 30 days after creation; the instance created on 20 November 2026 is scheduled to expire on **20 December 2026**. Export data or approve a suitable paid plan before that date if the team needs longer retention. No paid plan is selected here. Platform limits: [Render free instances](https://render.com/docs/free), [Blueprint specification](https://render.com/docs/blueprint-spec), [deployment checks](https://render.com/docs/deploys#integrating-with-ci).

## Local equivalent

Install the locked backend dependencies and editable backend, set `DATABASE_URL` and a randomly generated `JWT_SECRET` of at least 32 bytes in your shell, then run:

```sh
python -m fridgely_app migrate
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
python -m uvicorn fridgely_app.host:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` or `/api/docs`. If a connection is refused, verify the server process and its startup logs; a Vite dev server alone does not start Python. Browser tests use `backend/tests/serve_web_test.py`, whose controlled provider is intentionally separate from the cloud startup command.
