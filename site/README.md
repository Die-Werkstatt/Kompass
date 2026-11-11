# Website

`public/` is the whole site: one page, its fonts and favicon. Cloudflare
Workers serves it as static assets, with no Worker script (`wrangler.jsonc`).

`.github/workflows/site.yml` deploys it on every push to `main` that touches
`site/`, and when a release is published. A release's tag must be `v` plus the
manifest version, for example `v0.1.0`. The workflow builds `kompass-0.1.0.zip`
from the tag, attaches it to the release, copies it to `download/kompass.zip`
on the site and writes `download/index.json` with
`blender --command extension server-generate`. Dragging the Download Native
button into Blender installs the add-on and adds the site as a repository, so
Blender offers later releases as updates.

## Preview

```sh
cd site
npx wrangler@4.154.0 dev
```

## Set up Cloudflare once

1. In the Cloudflare dashboard, go to Account API tokens, select Create Token
   and use the Edit Cloudflare Workers template. Limit it to your account.
2. Copy your account ID from Workers & Pages > Account Details.
3. In GitHub, add both as repository secrets (Settings > Secrets and
   variables > Actions): `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
4. Run the site workflow (Actions > site > Run workflow). The first deploy
   creates the Worker `kompass-site` at `kompass-site.<subdomain>.workers.dev`.
5. For your own domain, the domain's zone must be on Cloudflare. In the
   Worker, go to Settings > Domains & Routes > Add > Custom Domain.
