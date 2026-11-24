# Cloud deployment

The deployable unit is one Docker web service containing the built React app, self-hosted Swagger UI and FastAPI host, connected to managed PostgreSQL 17. HTTPS terminates at Render. Frontend requests use `/api` on the same origin. Data never depends on the container's ephemeral filesystem.

`render.yaml` declares free resources in Frankfurt, a database reference for `DATABASE_URL`, a platform-generated `JWT_SECRET`, and readiness checks at `/api/health`. The existing `fridgely-web` service uses the original `SarpCizer/CMPE331-Project` repository and now follows **main**, with auto-deploy set to **After CI Checks Pass**, as recorded in [#40](https://github.com/SarpCizer/CMPE331-Project/issues/40). Its public URL is [https://fridgely-web.onrender.com](https://fridgely-web.onrender.com).

The committed Blueprint still selects `feature/berfin-cloud-candidate`; [#70](https://github.com/SarpCizer/CMPE331-Project/pull/70) proposes the change to `main`. Keep Blueprint auto-sync paused until the selected source and reviewed sync plan agree with the existing service. Reuse the existing free `fridgely-postgres` database. Review a Blueprint plan before applying it, particularly any proposed resource creation, deletion or database change.

The Docker build pins Node 24 / pnpm 11.25.0, frontend dependencies and Python runtime dependencies. The runtime runs as a non-root user. The start script explicitly applies the Alembic migration and then starts a single Uvicorn worker bound to `0.0.0.0:$PORT`. Importing the app does not run migrations. Concurrent Argon2 work is bounded to avoid unbounded password-hashing memory on the teaching instance. Database migrations are packaged in the installed wheel and apply successfully even when the source checkout is absent.

## Configure and deploy

1. Sign in to the team's Render workspace and open the existing [fridgely-web service](https://dashboard.render.com/web/srv-dc2qcjek1f9s738q5m80). Confirm its repository, `main` branch, free plan and successful deployed commit. Check that the commit includes the merged [Cloudflare adapter #65](https://github.com/SarpCizer/CMPE331-Project/pull/65).
2. Preserve the existing `DATABASE_URL` and `JWT_SECRET`. Creating a second web service or database is not part of activating the provider.
3. Configure the selected recipe provider in the web service's **Environment** settings and save/deploy. Follow the activation checks below.
4. After Render reports **Live**, verify `/`, `/api/health`, `/api/openapi.json` and `/api/docs`. Record the deployed commit and deploy link in #40. A passing CI run uses controlled providers and does not establish live inference.

Render's free service sleeps after 15 minutes without traffic and can take about a minute to wake. The free database expires 30 days after creation; the instance created on 20 November 2026 is scheduled to expire on **20 December 2026**. Export data or approve a suitable paid plan before that date if the team needs longer retention. No paid plan is selected here. Platform limits: [Render free instances](https://render.com/docs/free), [Blueprint specification](https://render.com/docs/blueprint-spec), [deployment checks](https://render.com/docs/deploys#integrating-with-ci).

## Recipe provider settings

For a free deployment, use a Cloudflare Workers Free account. Open **Workers AI → Use REST API** to get the account ID and create a Workers AI API token limited to the selected account. In Render, set `RECIPE_PROVIDER=cloudflare`, `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AI_TOKEN`. The adapter uses Llama 3.3 70B with JSON Mode. Workers Free includes 10,000 Neurons per day. Requests beyond the free allowance fail. Stay on Workers Free for this setup. [Token setup](https://developers.cloudflare.com/workers-ai/get-started/rest-api/) · [Free allowance](https://developers.cloudflare.com/workers-ai/platform/pricing/) · [Model](https://developers.cloudflare.com/workers-ai/models/llama-3.3-70b-instruct-fp8-fast/)

### Activate and verify Cloudflare

1. Sign in to the selected Cloudflare account and complete email verification if the dashboard requires it. Confirm **Workers Free** under **Workers plans**. The backend calls Workers AI's REST API directly; no Worker application or custom domain is required.
2. Open **Workers AI → REST API → Create a Workers AI API Token**. Name it for Fridgely, keep only **Workers AI Read** and **Workers AI Edit**, and restrict **Account Resources** to the selected account. Creating this credential grants ongoing inference access; review the selected account and permissions before submitting.
3. Copy the account ID and enter these variables directly into the existing Render service's **Environment** page:

   | Key | Value |
   | --- | --- |
   | `RECIPE_PROVIDER` | `cloudflare` |
   | `CLOUDFLARE_ACCOUNT_ID` | The selected account ID |
   | `CLOUDFLARE_AI_TOKEN` | The scoped token |

   Keep the token in Render's secret environment. Do not put its value in chat, GitHub, screenshots or reports. Choose **Save and deploy** after the adapter is present in the deployed build; use a new build when the selected source has changed.
4. Once the deployment is **Live**, use synthetic data in an authenticated account: add a few ingredients manually, record the inventory, and request one recipe batch. Open a returned recipe and add its missing ingredients to shopping. Verify the displayed results persist after reload and that generation, details and shopping actions leave the recorded inventory unchanged.
5. Confirm a second synthetic account cannot read the first account's recipe or shopping data. Record the exact source SHA, CI run, Render deploy, date, provider/model, observed result and any defect in #40. Exclude passwords, bearer tokens and provider credentials. Clean up only the synthetic records created for this check.

If generation fails, inspect sanitized server/provider errors and the account's quota. Preserve the observed failure and investigate it before declaring live AI complete. Keep the approved course-delivery ZIP/PDF pair pinned to its original source; a later application source requires matching verification and delivery artifacts.

For the existing OpenAI provider, set `RECIPE_PROVIDER=openai` and `OPENAI_API_KEY`. `OPENAI_MODEL` is optional. Both providers read credentials on the server. Store tokens in Render Environment and use synthetic data for the first live recipe check. A missing credential or upstream quota failure returns a retryable recipe error while account and inventory routes remain available.

## Local equivalent

Install the locked backend dependencies and editable backend, set `DATABASE_URL` and a randomly generated `JWT_SECRET` of at least 32 bytes in your shell, then run:

```sh
python -m fridgely_app migrate
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
python -m uvicorn fridgely_app.host:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` or `/api/docs`. If a connection is refused, verify the server process and its startup logs; a Vite dev server alone does not start Python. Browser tests use `backend/tests/serve_web_test.py`, whose controlled provider is intentionally separate from the cloud startup command.
