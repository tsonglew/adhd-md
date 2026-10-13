#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/adhd-md-package-check.XXXXXX")"
cleanup() {
  rm -rf "$tmp_root"
}
trap cleanup EXIT

pack_to() {
  local destination="$1"
  mkdir -p "$destination"
  (
    cd "$repo_root"
    npm_config_cache="$tmp_root/npm-cache" npm pack --ignore-scripts --json --pack-destination "$destination"
  ) > "$destination/pack-report.json"
  find "$destination" -maxdepth 1 -type f -name 'adhd-md-*.tgz' -print -quit
}

run_quiet() {
  local log_file="$1"
  shift
  if ! "$@" > "$log_file" 2>&1; then
    cat "$log_file" >&2
    return 1
  fi
}

run_project_tests() {
  (cd "$repo_root" && python3 -m unittest discover -s skill/scripts/tests)
}

before_dir="$tmp_root/before-tests"
before_tarball="$(pack_to "$before_dir")"
if [[ -z "$before_tarball" ]]; then
  printf '%s\n' "npm pack did not create the pre-test tarball" >&2
  exit 1
fi
tar -tzf "$before_tarball" | LC_ALL=C sort > "$tmp_root/files-before.txt"

# The suite creates bytecode caches in source directories. The nested ignore
# rules must keep those files out of the package without editing the source tree.
run_quiet "$tmp_root/source-tests.txt" run_project_tests
after_dir="$tmp_root/after-tests"
after_tarball="$(pack_to "$after_dir")"
if [[ -z "$after_tarball" ]]; then
  printf '%s\n' "npm pack did not create the post-test tarball" >&2
  exit 1
fi
tar -tzf "$after_tarball" | LC_ALL=C sort > "$tmp_root/files-after.txt"
if ! cmp -s "$tmp_root/files-before.txt" "$tmp_root/files-after.txt"; then
  printf '%s\n' "npm package contents changed after tests:" >&2
  diff -u "$tmp_root/files-before.txt" "$tmp_root/files-after.txt" >&2 || true
  exit 1
fi

contents="$tmp_root/contents.txt"
cp "$tmp_root/files-after.txt" "$contents"
required_files=(
  package.json
  LICENSE
  README.md
  CHANGELOG.md
  bin/cli.js
  scripts/install.sh
  skill/SKILL.md
  skill/assets/reader.html
  skill/references/reading.md
  skill/references/rules.md
  skill/references/rule-definitions.json
  skill/references/rubric.md
  skill/references/evidence.md
  skill/references/examples/README.md
  skill/scripts/adhd_md.py
  skill/scripts/extract_web.py
  skill/scripts/reader.py
  skill/scripts/sources.py
  skill/scripts/tests/test_reader.py
  skill/scripts/tests/test_install.py
  dist/adhd-md.standalone.md
)
for file in "${required_files[@]}"; do
  if ! grep -Fqx "package/$file" "$contents"; then
    printf 'npm tarball is missing required file: %s\n' "$file" >&2
    exit 1
  fi
done

if grep -Eq '(^|/)(__pycache__|node_modules|\.pytest_cache)/|\.py[cod]$|\.DS_Store$|\.tmp$|\.swp$|\.log$|(^|/)\.coverage$' "$contents"; then
  printf '%s\n' "npm tarball contains a cache or temporary file:" >&2
  grep -E '(^|/)(__pycache__|node_modules|\.pytest_cache)/|\.py[cod]$|\.DS_Store$|\.tmp$|\.swp$|\.log$|(^|/)\.coverage$' "$contents" >&2
  exit 1
fi

unpacked_root="$tmp_root/unpacked/_npx/package-check/node_modules"
mkdir -p "$unpacked_root"
tar -xzf "$after_tarball" -C "$unpacked_root"
mv "$unpacked_root/package" "$unpacked_root/adhd-md"
package_root="$unpacked_root/adhd-md"
expected_version="$(node -e 'process.stdout.write(require(process.argv[1]).version)' "$repo_root/package.json")"
actual_version="$(cd "$tmp_root" && node "$package_root/bin/cli.js" --version)"
if [[ "$actual_version" != "$expected_version" ]]; then
  printf 'packed CLI version mismatch: expected %s, got %s\n' "$expected_version" "$actual_version" >&2
  exit 1
fi

node_cli="$package_root/bin/cli.js"
sample="$tmp_root/sample.md"
original="$tmp_root/original.md"
html="$tmp_root/source.html"
extracted="$tmp_root/extracted.md"
reader="$tmp_root/reader.html"
cat > "$sample" <<'EOF'
# Package smoke check

The exact npm tarball must run audit, verify, read, extract, and install.

- The original text remains available.
- Each command writes only inside the temporary directory.
EOF
cp "$sample" "$original"
cat > "$html" <<'EOF'
<!doctype html><html><body><main><h1>Extracted title</h1><p>Local HTML content remains visible.</p></main></body></html>
EOF

remote_url="https://fixture.invalid/source.html"
cat > "$tmp_root/url-extract-smoke.py" <<'PY'
import runpy
import sys
from pathlib import Path

tool = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
scripts = tool.parent
sys.path.insert(0, str(scripts))
import extract_web

url = "https://fixture.invalid/source.html"
body = b"<!doctype html><html><body><main><h1>Extracted title</h1><p>URL extraction stays inside the packaged tool.</p></main></body></html>"

def fetch_url(requested, timeout=20):
    if requested != url:
        raise AssertionError("unexpected URL passed to the HTTP fixture")
    return {"body": body, "url": url, "content_type": "text/html", "charset": "utf-8"}

extract_web.fetch_url = fetch_url
sys.argv = [str(tool), "extract", url, "--output", str(output)]
runpy.run_path(str(tool), run_name="__main__")
PY

run_url_extract_smoke() {
  python3 "$tmp_root/url-extract-smoke.py" "$1" "$2"
}

node "$node_cli" --help > "$tmp_root/help.txt"
grep -Fq "adhd-md $expected_version" "$tmp_root/help.txt"
grep -Fq "npx github:tsonglew/adhd-md" "$tmp_root/help.txt"
if node "$node_cli" "$sample" > "$tmp_root/file-argument.txt" 2>&1; then
  printf '%s\n' "passing a filename directly should explain the supported invocation" >&2
  exit 1
fi
grep -Fq "npx github:tsonglew/adhd-md audit $sample" "$tmp_root/file-argument.txt"
node "$node_cli" audit "$sample" > "$tmp_root/audit.txt"
node "$node_cli" verify "$original" "$sample" --scope=format > "$tmp_root/verify.txt"
node "$node_cli" read "$sample" --output "$reader" > "$tmp_root/read.txt"
test -s "$reader"
grep -Fq "Package smoke check" "$reader"
node "$node_cli" extract "$html" --output "$extracted" > "$tmp_root/extract.txt"
test -s "$extracted"
grep -Fq "Local HTML content remains visible." "$extracted"
run_url_extract_smoke "$package_root/skill/scripts/adhd_md.py" "$tmp_root/remote-extracted.md" > "$tmp_root/remote-extract.txt"
grep -Fq "URL extraction stays inside the packaged tool." "$tmp_root/remote-extracted.md"
run_quiet "$tmp_root/packed-selftest.txt" node "$node_cli" selftest

# Exercise the package's default install path inside an isolated user root, then
# remove the unpacked package and run the copied skill's command surfaces again.
isolated_home="$tmp_root/install-home"
ADHD_MD_HOME="$isolated_home" node "$node_cli" install > "$tmp_root/install-output.txt"
grep -Fq "canonical skill → $isolated_home/.agents/skills/adhd-md" "$tmp_root/install-output.txt"
test -f "$isolated_home/.agents/skills/adhd-md/SKILL.md"
test ! -L "$isolated_home/.agents/skills/adhd-md"
test ! -e "$isolated_home/.agents/skills/.adhd-md-install.lock"
find "$isolated_home" -type l -print > "$tmp_root/installed-links.txt"
while IFS= read -r link; do
  target="$(readlink "$link")"
  case "$target" in "$package_root"/*|"$tmp_root/unpacked/"*) ;; *) continue ;; esac
  printf 'installed link points into temporary package storage: %s -> %s\n' "$link" "$target" >&2
  exit 1
done < "$tmp_root/installed-links.txt"
rm -rf "$tmp_root/unpacked"

installed_tool="$isolated_home/.agents/skills/adhd-md/scripts/adhd_md.py"
python3 "$installed_tool" audit "$sample" > "$tmp_root/installed-audit.txt"
python3 "$installed_tool" verify "$original" "$sample" --scope=format > "$tmp_root/installed-verify.txt"
python3 "$installed_tool" read "$sample" --output "$tmp_root/installed-reader.html" > "$tmp_root/installed-read.txt"
test -s "$tmp_root/installed-reader.html"
python3 "$installed_tool" extract "$html" --output "$tmp_root/installed-extracted.md" > "$tmp_root/installed-extract.txt"
grep -Fq "Local HTML content remains visible." "$tmp_root/installed-extracted.md"
run_url_extract_smoke "$installed_tool" "$tmp_root/installed-remote-extracted.md" > "$tmp_root/installed-remote-extract.txt"
grep -Fq "URL extraction stays inside the packaged tool." "$tmp_root/installed-remote-extracted.md"
run_quiet "$tmp_root/installed-selftest.txt" python3 "$installed_tool" selftest

file_count="$(wc -l < "$contents" | tr -d '[:space:]')"
printf 'npm tarball smoke passed: %s (%s files; manifests stable before/after tests)\n' "$(basename "$after_tarball")" "$file_count"
