#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() {
  printf 'harness validation failed: %s\n' "$1" >&2
  exit 1
}

required_files=(
  "AGENTS.md"
  "README.md"
  "docs/agent/index.md"
  "docs/agent/task-protocol.md"
  "docs/agent/validation.md"
  "docs/agent/doc-maintenance.md"
  "docs/agent/ui-ux-rules.md"
  "docs/agent/ai-feature-rules.md"
  "docs/agent/security-rules.md"
  "docs/agent/codex-routing.md"
  "docs/PRODUCT_VISION.md"
  "docs/architecture/index.md"
  "docs/architecture/boundaries.md"
  "docs/product/product-brief.md"
  "docs/product/user-journeys.md"
  "docs/exec-plans/template.md"
  "docs/quality/technical-debt.md"
  "docs/quality/quality-score.md"
  "docs/roadmap/task-map.md"
  "docs/roadmap/implementation-sequencing.md"
  "scripts/validate-harness.sh"
)

required_dirs=(
  "docs/architecture/decisions"
  "docs/exec-plans/active"
  "docs/exec-plans/completed"
)

for path in "${required_files[@]}"; do
  [[ -s "$path" ]] || fail "missing or empty required file: $path"
done

for path in "${required_dirs[@]}"; do
  [[ -d "$path" ]] || fail "missing required directory: $path"
  find "$path" -mindepth 1 -type f | grep -q . || fail "required directory has no files: $path"
done

if grep -R "TODO(project)" AGENTS.md docs README.md >/dev/null 2>&1; then
  fail "TODO(project) markers remain in tracked harness docs"
fi

if grep -R "docs/agents/" AGENTS.md docs README.md >/dev/null 2>&1; then
  fail "found stale docs/agents route; use docs/agent"
fi

if grep -R "\.codex/application_tracker\.toml" \
  AGENTS.md \
  docs/CODEX_CONFIGURATION.md \
  docs/CODEX_PLAYBOOK.md \
  docs/agent \
  >/dev/null 2>&1; then
  fail "found stale dependency on missing .codex/application_tracker.toml in the active routing surface"
fi

for route in \
  "docs/agent/index.md" \
  "docs/PRODUCT_VISION.md" \
  "docs/roadmap/implementation-sequencing.md" \
  "docs/roadmap/task-map.md" \
  "docs/product/product-brief.md" \
  "docs/product/user-journeys.md" \
  "docs/architecture/index.md" \
  "docs/architecture/boundaries.md" \
  "docs/agent/codex-routing.md" \
  "docs/agent/validation.md" \
  "docs/agent/doc-maintenance.md" \
  "docs/quality/technical-debt.md" \
  "docs/quality/quality-score.md"; do
  grep -q "$route" AGENTS.md || fail "AGENTS.md missing route: $route"
done

make_targets=(
  "lint"
  "test"
  "check"
  "migrate"
  "docker-import-smoke"
)

for target in "${make_targets[@]}"; do
  grep -Eq "^${target}:" Makefile || fail "Makefile missing documented target: ${target}"
done

printf 'harness validation passed\n'
