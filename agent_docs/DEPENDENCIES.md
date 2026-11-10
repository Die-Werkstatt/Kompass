# Kompass: dependency policy and inventory

A decision record, not a lockfile mirror. Every direct dependency gets one line
saying why it is here. Removed or rejected candidates go under "Removed" with
the reason, so the same discussion does not happen twice.

## Policy

- Prefer the standard library, then what is already in the tree.
- A new dependency needs a reason a reviewer can check: what it does that the
  tree cannot reasonably do itself, and what it gets access to.
- Dependabot opens update PRs weekly (`.github/dependabot.yml`).

## Current inventory

## Removed

| Dependency | Removed in | Why |
|---|---|---|
