# Website

`public/` is the whole site: one page, its fonts and favicon. Cloudflare Pages
serves it at `kompass-site.pages.dev` (`wrangler.jsonc`).

`.github/workflows/site.yml` deploys it on every push to `main` that touches
`site/`, and when a release is published. A release's tag must be `v` plus the
manifest version, for example `v0.1.0`. The workflow builds
`kompass-0.1.0.zip` and `kompass_native-0.1.0.zip` from the tag with
`build.py`, attaches both to the release, copies them to
`download/kompass.zip` and `download/kompass_native.zip` on the site and
writes `download/index.json` with `blender --command extension
server-generate`. Dragging a download button into Blender installs that
edition and adds the site as a repository, so Blender offers later releases
as updates.

## Preview

```sh
cd site
npx wrangler@4.154.0 pages dev
```

## Set up Cloudflare once

1. In the Cloudflare dashboard, go to Account API tokens and select Create
   Token > Custom token. Give it the permission Account > Cloudflare Pages >
   Edit, limited to your account.
2. Copy your account ID from Workers & Pages > Account Details.
3. In GitHub, add both as repository secrets (Settings > Secrets and
   variables > Actions): `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
4. Run the site workflow (Actions > site > Run workflow). The first run creates
   the Pages project `kompass-site`.
5. For your own domain, open the project in Workers & Pages and go to Custom
   domains > Set up a custom domain.
