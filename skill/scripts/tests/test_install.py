"""Scope checks for install.sh. All filesystem changes stay in temp roots."""

import os
import shutil
import subprocess
import tempfile
import tarfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
INSTALLER = REPO / "scripts" / "install.sh"
OWNER_TOKEN = "managed-by-adhd-md-install-v1"


def snapshot(root):
    """Capture the fixture tree, including broken symlinks and empty dirs."""
    state = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            state[relative] = ("symlink", os.readlink(path))
        elif path.is_dir():
            state[relative] = ("directory",)
        elif path.is_file():
            state[relative] = ("file", path.read_bytes())
    return state


@unittest.skipIf(os.name == "nt", "install.sh requires a Unix shell")
class InstallScopeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="adhd-md-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.install_home = self.root / "user-root"
        self.project = self.root / "project"
        self.project.mkdir()
        git = shutil.which("git")
        self.assertIsNotNone(git, "git is required for project-scoped install tests")
        subprocess.run([git, "init", "-q", str(self.project)], check=True)

        # Stub every external command the uninstall path can call. The rm stub
        # refuses any target outside the temporary root, including regressions
        # back to a hard-coded real HOME path.
        real_git = shutil.which("git")
        real_rm = shutil.which("rm")
        real_cat = shutil.which("cat")
        real_readlink = shutil.which("readlink")
        real_dirname = shutil.which("dirname")
        real_mkdir = shutil.which("mkdir")
        real_mv = shutil.which("mv")
        real_rmdir = shutil.which("rmdir")
        self.assertIsNotNone(real_git, "git is required for project-scoped install tests")
        self.assertIsNotNone(real_rm, "rm is required for uninstall tests")
        self.assertIsNotNone(real_cat, "cat is required for uninstall tests")
        self.assertIsNotNone(real_readlink, "readlink is required for uninstall tests")
        self.assertIsNotNone(real_dirname, "dirname is required for install-path tests")
        self.assertIsNotNone(real_mkdir, "mkdir is required for install-path tests")
        self.assertIsNotNone(real_mv, "mv is required for transactional installs")
        self.assertIsNotNone(real_rmdir, "rmdir is required for transaction recovery")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.write_command(
            "git",
            '#!/bin/sh\n'
            'if [ "$#" -ne 2 ] || [ "$1" != "rev-parse" ] || [ "$2" != "--show-toplevel" ]; then\n'
            '  echo "unexpected git command" >&2\n  exit 97\nfi\n'
            'exec "$ADHD_MD_REAL_GIT" "$@"\n',
        )
        self.write_command(
            "rm",
            '#!/bin/sh\n'
            'for target in "$@"; do\n'
            '  case "$target" in\n'
            '    -*) continue ;;\n'
            '    "$ADHD_MD_TEST_ROOT"/*) ;;\n'
            '    *) echo "refusing rm outside test root: $target" >&2; exit 97 ;;\n'
            '  esac\n'
            'done\n'
            'exec "$ADHD_MD_REAL_RM" "$@"\n',
        )
        self.write_command(
            "cat",
            '#!/bin/sh\n'
            'if [ "$#" -ne 0 ]; then echo "unexpected cat command" >&2; exit 97; fi\n'
            'exec "$ADHD_MD_REAL_CAT"\n',
        )
        self.write_command(
            "readlink",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe readlink input: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_READLINK" "$@"\n',
        )
        self.write_command(
            "dirname",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_INSTALLER_PATH"|"$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe dirname input: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_DIRNAME" "$@"\n',
        )
        self.write_command(
            "mkdir",
            '#!/bin/sh\n'
            'for target in "$@"; do case "$target" in -*) continue ;; "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe mkdir target: $target" >&2; exit 97 ;; esac; done\n'
            'exec "$ADHD_MD_REAL_MKDIR" "$@"\n',
        )
        self.write_command(
            "mv",
            '#!/bin/sh\n'
            'for target in "$@"; do case "$target" in -*) continue ;; "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe mv target: $target" >&2; exit 97 ;; esac; done\n'
            'exec "$ADHD_MD_REAL_MV" "$@"\n',
        )
        self.write_command(
            "rmdir",
            '#!/bin/sh\n'
            'for target in "$@"; do case "$target" in -*) continue ;; "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe rmdir target: $target" >&2; exit 97 ;; esac; done\n'
            'exec "$ADHD_MD_REAL_RMDIR" "$@"\n',
        )
        self.env = os.environ.copy()
        self.env["ADHD_MD_HOME"] = str(self.install_home)
        self.env["HOME"] = str(self.install_home)
        self.env["ADHD_MD_TEST_ROOT"] = str(self.root)
        self.env["ADHD_MD_REAL_GIT"] = real_git
        self.env["ADHD_MD_REAL_RM"] = real_rm
        self.env["ADHD_MD_REAL_CAT"] = real_cat
        self.env["ADHD_MD_REAL_READLINK"] = real_readlink
        self.env["ADHD_MD_REAL_DIRNAME"] = real_dirname
        self.env["ADHD_MD_REAL_MKDIR"] = real_mkdir
        self.env["ADHD_MD_REAL_MV"] = real_mv
        self.env["ADHD_MD_REAL_RMDIR"] = real_rmdir
        self.env["ADHD_MD_INSTALLER_PATH"] = str(INSTALLER)
        self.env["PATH"] = str(self.bin)

    def write_command(self, name, content):
        command = self.bin / name
        command.write_text(content, encoding="utf-8")
        command.chmod(0o755)

    def add_filesystem_install_stubs(self):
        for name in ("mkdir", "cp", "ln", "mv"):
            real = shutil.which(name)
            self.assertIsNotNone(real, f"{name} is required for install fixtures")
            key = name.upper()
            self.env[f"ADHD_MD_REAL_{key}"] = real
            if name == "cp":
                body = (
                    '#!/bin/sh\n'
                    'for arg in "$@"; do dest="$arg"; done\n'
                    'case "$dest" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe cp destination: $dest" >&2; exit 97 ;; esac\n'
                    'if [ -n "${ADHD_MD_FAIL_CP_MATCH:-}" ]; then case "$dest" in ${ADHD_MD_FAIL_CP_MATCH}) exit 91 ;; esac; fi\n'
                )
            elif name == "mv":
                body = (
                    '#!/bin/sh\n'
                    'is_stage=0; selected_dest=""\n'
                    'for arg in "$@"; do case "$arg" in *.adhd-md-stage-*) is_stage=1 ;; esac; selected_dest="$arg"; done\n'
                    'for var in ADHD_MD_FAIL_MV_DEST ADHD_MD_INTERRUPT_MV_DEST; do\n'
                    '  eval wanted="\\${$var:-}"\n'
                    '  if [ "$is_stage" = 1 ] && [ -n "$wanted" ] && [ "$selected_dest" = "$wanted" ]; then\n'
                    '    if [ "$var" = ADHD_MD_INTERRUPT_MV_DEST ]; then kill -TERM "$PPID"; else exit 92; fi\n'
                    '  fi\n'
                    'done\n'
                    'for arg in "$@"; do case "$arg" in -*) continue ;; "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe mv target: $arg" >&2; exit 97 ;; esac; done\n'
                )
            else:
                body = (
                    '#!/bin/sh\n'
                    'for target in "$@"; do\n'
                    '  case "$target" in -*) continue ;; "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe '
                    + name
                    + ' target: $target" >&2; exit 97 ;; esac\n'
                    'done\n'
                )
            self.write_command(name, body + f'exec "$ADHD_MD_REAL_{key}" "$@"\n')

    def add_python_install_stub(self, allowed_script, log_path=None):
        real = shutil.which("python3")
        self.assertIsNotNone(real, "python3 is required for install fixtures")
        self.env["ADHD_MD_REAL_PYTHON"] = real
        self.env["ADHD_MD_ALLOWED_PYTHON_SCRIPT"] = str(allowed_script)
        if log_path is not None:
            self.env["ADHD_MD_PYTHON_LOG"] = str(log_path)
        log_line = 'printf "%s\\n" "$*" >> "$ADHD_MD_PYTHON_LOG"\n' if log_path is not None else ""
        self.write_command(
            "python3",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_TEST_ROOT"/*/scripts/adhd_md.py) ;; *) echo "unsafe Python invocation: $*" >&2; exit 97 ;; esac\n'
            'if [ "${ADHD_MD_FAIL_STAGED_SELFTEST:-0}" = 1 ]; then case "$1" in *.adhd-md-stage-*/scripts/adhd_md.py) exit 93 ;; esac; fi\n'
            'if [ "$2" != "selftest" ]; then echo "unsafe Python invocation: $*" >&2; exit 97; fi\n'
            + log_line
            + 'exit 0\n',
        )

    def prepare_npx_installer(self, with_codex=False):
        package = self.root / "npm-cache" / "_npx" / "fake-hash" / "node_modules" / "adhd-md"
        package.mkdir(parents=True)
        shutil.copytree(REPO / "skill", package / "skill")
        (package / "scripts").mkdir()
        shutil.copy2(INSTALLER, package / "scripts" / "install.sh")
        self.add_filesystem_install_stubs()
        self.add_python_install_stub(package / "skill" / "scripts" / "adhd_md.py")
        self.write_command("claude", "#!/bin/sh\nexit 0\n")
        if with_codex:
            self.write_command("codex", "#!/bin/sh\nexit 0\n")

        def install():
            return subprocess.run(
                ["/bin/bash", str(package / "scripts" / "install.sh")],
                cwd=self.project,
                env=self.env,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
            )

        first = install()
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout[-1000:])
        return package, install

    def prepare_project_installer(self, with_claude=True):
        if with_claude:
            (self.project / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
        self.env.update({
            "ADHD_MD_INSTALL_SOURCE": str(REPO / "skill"),
            "ADHD_MD_PROJECT_ROOT": str(self.project),
            "ADHD_MD_REAL_PYTHON": shutil.which("python3"),
        })
        self.add_filesystem_install_stubs()
        self.write_command(
            "python3",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_INSTALL_SOURCE/scripts/adhd_md.py"|"$ADHD_MD_PROJECT_ROOT"/.agents/skills/.adhd-md.adhd-md-stage-*/scripts/adhd_md.py) ;; *) echo "unsafe Python script: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_PYTHON" "$@"\n',
        )

        def install(*args):
            return subprocess.run(
                ["/bin/bash", str(INSTALLER), *args],
                cwd=self.project,
                env=self.env,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
            )

        first = install("--project")
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout[-1000:])
        return install

    def run_uninstall(self, *args):
        return subprocess.run(
            ["/bin/bash", str(INSTALLER), *args, "--uninstall"],
            cwd=self.project,
            env=self.env,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
        )

    def seed_user_prompt(self):
        prompt = self.install_home / ".codex" / "prompts" / "adhd-md.md"
        prompt.parent.mkdir(parents=True)
        prompt.write_text("user-level prompt\n", encoding="utf-8")
        return prompt

    def seed_project_skill(self, managed=True, host="claude"):
        skill = self.project / f".{host}" / "skills" / "adhd-md"
        skill.mkdir(parents=True)
        marker = skill / "project-skill.txt"
        marker.write_text("project-level skill\n", encoding="utf-8")
        if managed:
            (skill / ".adhd-md-managed").write_text(OWNER_TOKEN + "\n", encoding="utf-8")
        return skill, marker

    def seed_project_canonical(self, managed=True):
        canonical = self.project / ".agents" / "skills" / "adhd-md"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("project canonical\n", encoding="utf-8")
        owner = canonical.parent / ".adhd-md-managed-canonical"
        if managed:
            owner.write_text(OWNER_TOKEN + "\n", encoding="utf-8")
        return canonical, owner

    def test_project_uninstall_dry_run_omits_user_prompt(self):
        prompt = self.seed_user_prompt()
        skill, _ = self.seed_project_skill()
        before = snapshot(self.root)

        result = self.run_uninstall("--project", "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(str(prompt), result.stdout)
        self.assertEqual(snapshot(self.root), before)
        self.assertTrue(skill.is_dir())

    def test_project_uninstall_removes_project_skill_and_keeps_user_prompt(self):
        prompt = self.seed_user_prompt()
        skill, _ = self.seed_project_skill()
        canonical, _ = self.seed_project_canonical()
        other_project = self.root / "other-project"
        other_project.mkdir()
        other_git = shutil.which("git")
        subprocess.run([other_git, "init", "-q", str(other_project)], check=True)
        other_marker = other_project / ".grok" / "skills" / "adhd-md" / "project-skill.txt"
        other_marker.parent.mkdir(parents=True)
        other_marker.write_text("other project skill\n", encoding="utf-8")

        result = self.run_uninstall("--project")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(skill.exists())
        self.assertFalse(canonical.exists())
        self.assertEqual(prompt.read_text(encoding="utf-8"), "user-level prompt\n")
        self.assertEqual(other_marker.read_text(encoding="utf-8"), "other project skill\n")

    def test_user_uninstall_keeps_project_skill(self):
        prompt = self.seed_user_prompt()
        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        canonical.mkdir(parents=True)
        (canonical / "skill.txt").write_text("user-level skill\n", encoding="utf-8")
        (canonical.parent / ".adhd-md-managed-canonical").write_text(OWNER_TOKEN + "\n", encoding="utf-8")
        _, project_marker = self.seed_project_skill()

        result = self.run_uninstall()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(prompt.exists())
        self.assertFalse(canonical.exists())
        self.assertEqual(project_marker.read_text(encoding="utf-8"), "project-level skill\n")

    def test_repeated_user_uninstall_is_idempotent(self):
        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        canonical.mkdir(parents=True)
        (self.install_home / ".agents" / "skills" / ".adhd-md-managed-canonical").write_text(
            OWNER_TOKEN + "\n", encoding="utf-8"
        )
        (canonical / "skill.txt").write_text("installed skill\n", encoding="utf-8")
        for rel in (
            ".claude/skills/adhd-md",
            ".codex/skills/adhd-md",
            ".grok/skills/adhd-md",
            ".gemini/skills/adhd-md",
            ".cursor/skills/adhd-md",
            ".config/opencode/skills/adhd-md",
        ):
            link = self.install_home / rel
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(canonical)
        prompt = self.seed_user_prompt()

        first = self.run_uninstall()
        after_first = snapshot(self.root)
        second = self.run_uninstall()

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertFalse(canonical.exists())
        self.assertFalse(prompt.exists())
        self.assertEqual(snapshot(self.root), after_first)

    def test_host_table_handles_cli_alias_directory_only_and_no_hosts(self):
        claude = self.bin / "claude"
        self.write_command("claude", "#!/bin/sh\nexit 0\n")
        before = snapshot(self.root)
        cli_only = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--dry-run"],
            cwd=self.project,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cli_only.returncode, 0, cli_only.stderr)
        self.assertRegex(cli_only.stdout, r"(?m)^  claude\s+✓")
        self.assertEqual(snapshot(self.root), before)

        self.write_command("grok", "#!/bin/sh\nexit 0\n")
        self.write_command("cursor-agent", "#!/bin/sh\nexit 0\n")
        self.write_command("cursor", "#!/bin/sh\nexit 0\n")
        before = snapshot(self.root)
        multiple_hosts = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--dry-run"],
            cwd=self.project,
            env=self.env,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
        )
        self.assertEqual(multiple_hosts.returncode, 0, multiple_hosts.stderr)
        self.assertRegex(multiple_hosts.stdout, r"(?m)^  claude\s+✓")
        self.assertRegex(multiple_hosts.stdout, r"(?m)^  grok\s+✓")
        self.assertRegex(multiple_hosts.stdout, r"(?m)^  cursor-agent\s+✓")
        self.assertEqual(snapshot(self.root), before)

        claude.unlink()
        (self.bin / "grok").unlink()
        (self.bin / "cursor-agent").unlink()
        legacy_cursor = self.bin / "cursor"
        before = snapshot(self.root)
        cursor_alias = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--dry-run"],
            cwd=self.project,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cursor_alias.returncode, 0, cursor_alias.stderr)
        self.assertRegex(cursor_alias.stdout, r"(?m)^  cursor\s+✓")
        self.assertIn(".cursor/skills/adhd-md", cursor_alias.stdout)
        self.assertEqual(snapshot(self.root), before)

        legacy_cursor.unlink()
        cursor_dir = self.install_home / ".cursor" / "skills"
        cursor_dir.mkdir(parents=True)
        before = snapshot(self.root)
        directory_only = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--dry-run"],
            cwd=self.project,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(directory_only.returncode, 0, directory_only.stderr)
        self.assertRegex(directory_only.stdout, r"(?m)^  cursor\s+✓")
        self.assertEqual(snapshot(self.root), before)

        shutil.rmtree(cursor_dir.parent)
        before = snapshot(self.root)
        no_hosts = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--dry-run"],
            cwd=self.project,
            env=self.env,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
        )
        self.assertEqual(no_hosts.returncode, 0, no_hosts.stderr + no_hosts.stdout)
        self.assertIn("没检测到已安装的宿主 CLI 或 skills 目录", no_hosts.stdout)
        self.assertEqual(snapshot(self.root), before)

    def test_npx_cache_install_copies_to_stable_user_root(self):
        package = self.root / "npm-cache" / "_npx" / "fake-hash" / "node_modules" / "adhd-md"
        package.mkdir(parents=True)
        shutil.copytree(REPO / "skill", package / "skill")
        (package / "scripts").mkdir()
        shutil.copy2(INSTALLER, package / "scripts" / "install.sh")
        self.add_filesystem_install_stubs()
        python_log = self.root / "python.log"
        self.add_python_install_stub(package / "skill" / "scripts" / "adhd_md.py", python_log)
        self.write_command("claude", "#!/bin/sh\nexit 0\n")

        result = subprocess.run(
            ["/bin/bash", str(package / "scripts" / "install.sh")],
            cwd=self.project,
            env=self.env,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
        )

        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        host_link = self.install_home / ".claude" / "skills" / "adhd-md"
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout[-1000:])
        self.assertIn("从 npx 缓存运行，改用复制", result.stdout)
        self.assertFalse(canonical.is_symlink())
        self.assertTrue(host_link.is_symlink())
        self.assertEqual(host_link.resolve(), canonical)
        self.assertIn("selftest", python_log.read_text(encoding="utf-8"))

        shutil.rmtree(self.root / "npm-cache")
        self.assertTrue((canonical / "SKILL.md").is_file())
        self.assertEqual(host_link.resolve(), canonical)

    def test_git_clone_link_mode_updates_through_reinstall(self):
        clone = self.root / "clone"
        shutil.copytree(REPO / "skill", clone / "skill")
        (clone / "scripts").mkdir()
        shutil.copy2(INSTALLER, clone / "scripts" / "install.sh")
        subprocess.run([shutil.which("git"), "init", "-q", str(clone)], check=True)
        self.add_filesystem_install_stubs()
        self.add_python_install_stub(clone / "skill" / "scripts" / "adhd_md.py")
        self.write_command("claude", "#!/bin/sh\nexit 0\n")

        def install_from_clone():
            return subprocess.run(
                ["/bin/bash", str(clone / "scripts" / "install.sh")],
                cwd=self.project,
                env=self.env,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
            )

        first = install_from_clone()
        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        host_link = self.install_home / ".claude" / "skills" / "adhd-md"
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout[-1000:])
        self.assertTrue(canonical.is_symlink())
        self.assertEqual(canonical.resolve(), clone / "skill")
        self.assertTrue(host_link.is_symlink())
        self.assertEqual(host_link.resolve(), clone / "skill")

        skill_doc = clone / "skill" / "SKILL.md"
        skill_doc.write_text(skill_doc.read_text(encoding="utf-8") + "\n<!-- clone update -->\n", encoding="utf-8")
        second = install_from_clone()
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout[-1000:])
        self.assertEqual(canonical.resolve(), clone / "skill")
        self.assertEqual(host_link.resolve(), clone / "skill")
        self.assertIn("<!-- clone update -->", (host_link / "SKILL.md").read_text(encoding="utf-8"))

    def test_user_uninstall_removes_owned_dangling_link_and_keeps_foreign_one(self):
        skills = self.install_home / ".claude" / "skills"
        skills.mkdir(parents=True)
        expected_dangling = skills / "adhd-md"
        expected_canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        expected_dangling.symlink_to(expected_canonical)
        foreign_dir = self.install_home / ".grok" / "skills"
        foreign_dir.mkdir(parents=True)
        foreign_dangling = foreign_dir / "adhd-md"
        foreign_dangling.symlink_to(self.install_home / "some-other-skill")

        result = self.run_uninstall()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(expected_dangling.is_symlink())
        self.assertTrue(foreign_dangling.is_symlink())
        self.assertIn("保留非本工具 canonical 链接", result.stdout)

    def test_partial_installs_remove_only_assets_with_ownership_evidence(self):
        managed, _ = self.seed_project_skill(managed=True, host="claude")
        partial, partial_marker = self.seed_project_skill(managed=False, host="grok")
        project_canonical, _ = self.seed_project_canonical(managed=False)

        project_result = self.run_uninstall("--project")

        self.assertEqual(project_result.returncode, 0, project_result.stderr)
        self.assertFalse(managed.exists())
        self.assertTrue(partial.is_dir())
        self.assertTrue(project_canonical.is_dir())
        self.assertEqual(partial_marker.read_text(encoding="utf-8"), "project-level skill\n")
        self.assertIn("保留无法确认归属的项目目录", project_result.stdout)
        self.assertIn("保留无法确认归属的项目 canonical", project_result.stdout)

        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        canonical.mkdir(parents=True)
        (canonical / "partial.txt").write_text("unowned partial install\n", encoding="utf-8")
        host_dir = self.install_home / ".claude" / "skills" / "adhd-md"
        host_dir.mkdir(parents=True)
        (host_dir / "user-file.txt").write_text("keep me\n", encoding="utf-8")

        user_result = self.run_uninstall()

        self.assertEqual(user_result.returncode, 0, user_result.stderr)
        self.assertTrue(canonical.is_dir())
        self.assertTrue((canonical / "partial.txt").exists())
        self.assertTrue(host_dir.is_dir())
        self.assertTrue((host_dir / "user-file.txt").exists())
        self.assertIn("保留无法确认归属的 canonical 目录", user_result.stdout)
        self.assertIn("保留无法确认归属的宿主目录", user_result.stdout)

    def test_project_install_marks_copy_for_scoped_uninstall(self):
        (self.project / ".claude" / "skills").mkdir(parents=True)
        real = {}
        for name in ("python3", "mkdir", "cp"):
            path = shutil.which(name)
            self.assertIsNotNone(path, f"{name} is required for the project install fixture")
            real[name] = path
        self.env.update({
            "ADHD_MD_INSTALL_SOURCE": str(REPO / "skill"),
            "ADHD_MD_PROJECT_ROOT": str(self.project),
            "ADHD_MD_REAL_PYTHON": shutil.which("python3"),
        })
        self.write_command(
            "python3",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_INSTALL_SOURCE/scripts/adhd_md.py"|"$ADHD_MD_PROJECT_ROOT"/.agents/skills/.adhd-md.adhd-md-stage-*/scripts/adhd_md.py) ;; *) echo "unsafe Python script: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_PYTHON" "$@"\n',
        )
        self.add_filesystem_install_stubs()
        real_dirname = shutil.which("dirname")
        self.assertIsNotNone(real_dirname, "dirname is required for the project install fixture")
        self.env["ADHD_MD_REAL_DIRNAME"] = real_dirname
        self.write_command(
            "dirname",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_INSTALLER_PATH"|"$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe dirname input: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_DIRNAME" "$@"\n',
        )
        self.env["ADHD_MD_INSTALLER_PATH"] = str(INSTALLER)

        install = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--project"],
            cwd=self.project,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

        target = self.project / ".claude" / "skills" / "adhd-md"
        canonical = self.project / ".agents" / "skills" / "adhd-md"
        self.assertEqual(install.returncode, 0, install.stderr + install.stdout[-1000:])
        self.assertIn(str(canonical), install.stdout)
        self.assertTrue((canonical / "SKILL.md").is_file())
        self.assertEqual((canonical.parent / ".adhd-md-managed-canonical").read_text(encoding="utf-8"), OWNER_TOKEN + "\n")
        self.assertEqual((target / ".adhd-md-managed").read_text(encoding="utf-8"), OWNER_TOKEN + "\n")
        removed = self.run_uninstall("--project")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertFalse(target.exists())
        self.assertFalse(canonical.exists())

    def test_copy_failure_preserves_previous_npx_install(self):
        package, install = self.prepare_npx_installer()
        source_doc = package / "skill" / "SKILL.md"
        source_doc.write_text(source_doc.read_text(encoding="utf-8") + "\nnew release\n", encoding="utf-8")
        before = snapshot(self.root)
        self.env["ADHD_MD_FAIL_CP_MATCH"] = "*adhd-md-stage-*"

        result = install()

        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        self.assertEqual(result.returncode, 91, result.stderr + result.stdout[-1000:])
        self.assertEqual(snapshot(self.root), before)
        self.assertNotIn("new release", (canonical / "SKILL.md").read_text(encoding="utf-8"))
        self.assertFalse((canonical.parent / ".adhd-md-install.lock").exists())

    def test_staged_selftest_failure_preserves_previous_install(self):
        package, install = self.prepare_npx_installer()
        source_doc = package / "skill" / "SKILL.md"
        source_doc.write_text(source_doc.read_text(encoding="utf-8") + "\nnew release\n", encoding="utf-8")
        before = snapshot(self.root)
        self.env["ADHD_MD_FAIL_STAGED_SELFTEST"] = "1"

        result = install()

        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout[-1000:])
        self.assertEqual(snapshot(self.root), before)
        self.assertNotIn("new release", (canonical / "SKILL.md").read_text(encoding="utf-8"))

    def test_switch_failure_restores_all_project_assets(self):
        install = self.prepare_project_installer()
        before = snapshot(self.root)
        failing_target = self.project / ".claude" / "skills" / "adhd-md"
        self.env["ADHD_MD_FAIL_MV_DEST"] = str(failing_target)

        result = install("--project")

        self.assertEqual(result.returncode, 92, result.stderr + result.stdout[-1000:])
        self.assertEqual(snapshot(self.root), before)

    def test_user_host_links_and_codex_prompt_roll_back_together(self):
        package, install = self.prepare_npx_installer(with_codex=True)
        source_doc = package / "skill" / "SKILL.md"
        source_doc.write_text(source_doc.read_text(encoding="utf-8") + "\nnew release\n", encoding="utf-8")
        before = snapshot(self.root)
        prompt = self.install_home / ".codex" / "prompts" / "adhd-md.md"
        self.env["ADHD_MD_FAIL_MV_DEST"] = str(prompt)

        result = install()

        host_link = self.install_home / ".codex" / "skills" / "adhd-md"
        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        self.assertEqual(result.returncode, 92, result.stderr + result.stdout[-1000:])
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(host_link.resolve(), canonical)

    def test_sigterm_during_switch_restores_previous_project_assets(self):
        install = self.prepare_project_installer()
        before = snapshot(self.root)
        failing_target = self.project / ".claude" / "skills" / "adhd-md"
        self.env["ADHD_MD_INTERRUPT_MV_DEST"] = str(failing_target)

        result = install("--project")

        self.assertEqual(result.returncode, 143, result.stderr + result.stdout[-1000:])
        self.assertEqual(snapshot(self.root), before)

    def test_concurrent_install_refuses_to_write_under_live_lock(self):
        _, install = self.prepare_npx_installer()
        lock = self.install_home / ".agents" / "skills" / ".adhd-md-install.lock"
        lock.mkdir()
        (lock / "owner").write_text(f"{OWNER_TOKEN}\n{os.getpid()}\n", encoding="utf-8")
        before = snapshot(self.root)

        result = install()

        self.assertEqual(result.returncode, 75, result.stderr + result.stdout[-1000:])
        self.assertIn("另一个安装器正在运行", result.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_stale_active_transaction_is_recovered_before_retry(self):
        canonical = self.project / ".agents" / "skills" / "adhd-md"
        canonical.parent.mkdir(parents=True)
        canonical.mkdir()
        (canonical / "old.txt").write_text("old complete installation\n", encoding="utf-8")
        owner_marker = canonical.parent / ".adhd-md-managed-canonical"
        owner_marker.write_text(OWNER_TOKEN + "\n", encoding="utf-8")

        lock = canonical.parent / ".adhd-md-install.lock"
        lock.mkdir()
        (lock / "owner").write_text(f"{OWNER_TOKEN}\n99999999\n", encoding="utf-8")
        (lock / "state").write_text("active\n", encoding="utf-8")
        backup = canonical.parent / ".adhd-md.adhd-md-backup-interrupted-0"
        stage = canonical.parent / ".adhd-md.adhd-md-stage-interrupted-0"
        canonical.rename(backup)
        canonical.mkdir()
        (canonical / "partial.txt").write_text("incomplete new installation\n", encoding="utf-8")
        (lock / "targets").write_bytes(
            os.fsencode(canonical) + b"\0" + os.fsencode(backup) + b"\0" + os.fsencode(stage) + b"\0" + b"1\0"
        )

        self.env.update({
            "ADHD_MD_INSTALL_SOURCE": str(REPO / "skill"),
            "ADHD_MD_PROJECT_ROOT": str(self.project),
            "ADHD_MD_REAL_PYTHON": shutil.which("python3"),
            "ADHD_MD_FAIL_CP_MATCH": "*adhd-md-stage-*",
        })
        self.add_filesystem_install_stubs()
        self.write_command(
            "python3",
            '#!/bin/sh\n'
            'exec "$ADHD_MD_REAL_PYTHON" "$@"\n',
        )
        result = subprocess.run(
            ["/bin/bash", str(INSTALLER), "--project"],
            cwd=self.project,
            env=self.env,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 91, result.stderr + result.stdout[-1000:])
        self.assertIn("已恢复上次中断的安装事务", result.stderr)
        self.assertEqual((canonical / "old.txt").read_text(encoding="utf-8"), "old complete installation\n")
        self.assertFalse((canonical / "partial.txt").exists())
        self.assertFalse(backup.exists())
        self.assertFalse(lock.exists())

    def test_remote_install_uses_local_tarball_and_stays_in_temp_root(self):
        tarball = self.root / "source.tar.gz"
        git = shutil.which("git")
        tracked = subprocess.run(
            [git, "ls-files", "-z", "--", "skill", "adapters/codex"],
            cwd=REPO,
            check=True,
            capture_output=True,
        ).stdout.split(b"\0")
        # Include newly introduced source files in the simulated committed tarball.
        # `git ls-files` omits them until the user stages a commit, but the hosted
        # tarball after merge will contain every versioned skill file.
        archive_paths = {Path(os.fsdecode(raw)) for raw in tracked if raw}
        archive_paths.add(Path("skill/references/rule-definitions.json"))
        with tarfile.open(tarball, "w:gz") as archive:
            for rel in sorted(archive_paths):
                archive.add(REPO / rel, arcname=Path("adhd-md-main") / rel, recursive=False)

        real = {}
        for name in ("tar", "mktemp", "python3", "mkdir", "cp", "ln", "mv", "sed", "dirname", "cat"):
            path = shutil.which(name)
            self.assertIsNotNone(path, f"{name} is required for the local tarball fixture")
            real[name] = path

        tmpdir = self.root / "tmp"
        tmpdir.mkdir()
        curl_log = self.root / "curl.log"
        temp_log = self.root / "mktemp.log"
        curl_log.write_text("", encoding="utf-8")
        temp_log.write_text("", encoding="utf-8")

        self.write_command(
            "curl",
            '#!/bin/sh\n'
            'if [ "$#" -ne 2 ] || [ "$1" != "-fsSL" ] || [ "$2" != "$ADHD_MD_EXPECTED_TARBALL_URL" ]; then\n'
            '  echo "unexpected curl request" >&2; exit 97\nfi\n'
            'printf "%s\\n" "$*" >> "$ADHD_MD_CURL_LOG"\n'
            'exec "$ADHD_MD_REAL_CAT" "$ADHD_MD_TEST_TARBALL"\n',
        )
        self.write_command(
            "tar",
            '#!/bin/sh\n'
            'extract_dir=""; next_is_dir=0\n'
            'for arg in "$@"; do\n'
            '  if [ "$next_is_dir" = 1 ]; then extract_dir="$arg"; next_is_dir=0; fi\n'
            '  [ "$arg" = "-C" ] && next_is_dir=1\n'
            'done\n'
            'case "$extract_dir" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe tar target: $extract_dir" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_TAR" "$@"\n',
        )
        self.write_command(
            "mktemp",
            '#!/bin/sh\n'
            'case "$TMPDIR" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe TMPDIR: $TMPDIR" >&2; exit 97 ;; esac\n'
            'created="$("$ADHD_MD_REAL_MKTEMP" "$@")" || exit $?\n'
            'printf "%s\\n" "$created" >> "$ADHD_MD_MKTEMP_LOG"\n'
            'printf "%s\\n" "$created"\n',
        )
        self.write_command(
            "python3",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe Python script: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_PYTHON" "$@"\n',
        )
        self.write_command(
            "dirname",
            '#!/bin/sh\n'
            'case "$1" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe dirname input: $1" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_DIRNAME" "$@"\n',
        )
        for name, real_name in (("mkdir", "MKDIR"), ("cp", "CP"), ("ln", "LN"), ("mv", "MV")):
            self.write_command(
                name,
                '#!/bin/sh\n'
                'for target in "$@"; do\n'
                '  case "$target" in -*) continue ;; "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe '
                + name
                + ' target: $target" >&2; exit 97 ;; esac\n'
                'done\n'
                'exec "$ADHD_MD_REAL_'
                + real_name
                + '" "$@"\n',
            )
        self.write_command(
            "sed",
            '#!/bin/sh\n'
            'for arg in "$@"; do source_file="$arg"; done\n'
            'case "$source_file" in "$ADHD_MD_TEST_ROOT"/*) ;; *) echo "unsafe sed input: $source_file" >&2; exit 97 ;; esac\n'
            'exec "$ADHD_MD_REAL_SED" "$@"\n',
        )
        for host in ("claude", "codex", "grok", "gemini", "cursor-agent", "opencode"):
            self.write_command(host, "#!/bin/sh\nexit 0\n")

        env = self.env.copy()
        env.update({
            "ADHD_MD_TEST_TARBALL": str(tarball),
            "ADHD_MD_EXPECTED_TARBALL_URL": "https://codeload.github.com/tsonglew/adhd-md/tar.gz/refs/heads/main",
            "ADHD_MD_CURL_LOG": str(curl_log),
            "ADHD_MD_MKTEMP_LOG": str(temp_log),
            "ADHD_MD_REAL_CAT": real["cat"],
            "ADHD_MD_REAL_TAR": real["tar"],
            "ADHD_MD_REAL_MKTEMP": real["mktemp"],
            "ADHD_MD_REAL_PYTHON": real["python3"],
            "ADHD_MD_REAL_MKDIR": real["mkdir"],
            "ADHD_MD_REAL_CP": real["cp"],
            "ADHD_MD_REAL_LN": real["ln"],
            "ADHD_MD_REAL_MV": real["mv"],
            "ADHD_MD_REAL_SED": real["sed"],
            "ADHD_MD_REAL_DIRNAME": real["dirname"],
            "TMPDIR": str(tmpdir),
            "PATH": str(self.bin),
        })
        result = subprocess.run(
            ["/bin/bash", "-s"],
            input=INSTALLER.read_text(encoding="utf-8"),
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout[-2000:])
        self.assertEqual(len(curl_log.read_text(encoding="utf-8").splitlines()), 1)
        self.assertEqual(len(temp_log.read_text(encoding="utf-8").splitlines()), 1)
        extracted = Path(temp_log.read_text(encoding="utf-8").strip())
        self.assertFalse(extracted.exists(), "remote source staging directory must be cleaned")

        canonical = self.install_home / ".agents" / "skills" / "adhd-md"
        self.assertTrue((canonical / "scripts" / "adhd_md.py").is_file())
        self.assertTrue((canonical / "references" / "rules.md").is_file())
        for rel in (
            ".claude/skills/adhd-md",
            ".codex/skills/adhd-md",
            ".grok/skills/adhd-md",
            ".gemini/skills/adhd-md",
            ".cursor/skills/adhd-md",
            ".config/opencode/skills/adhd-md",
        ):
            link = self.install_home / rel
            self.assertTrue(link.is_symlink(), rel)
            self.assertEqual(link.resolve(), canonical, rel)
        prompt = self.install_home / ".codex" / "prompts" / "adhd-md.md"
        self.assertIn(str(canonical / "SKILL.md"), prompt.read_text(encoding="utf-8"))

        project_result = subprocess.run(
            ["/bin/bash", "-s", "--", "--project"],
            input=INSTALLER.read_text(encoding="utf-8"),
            cwd=self.project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(project_result.returncode, 0, project_result.stderr + project_result.stdout[-2000:])
        self.assertEqual(len(curl_log.read_text(encoding="utf-8").splitlines()), 2)
        extracted_paths = [Path(path) for path in temp_log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(extracted_paths), 2)
        self.assertTrue(all(not path.exists() for path in extracted_paths))

        project_canonical = self.project / ".agents" / "skills" / "adhd-md"
        self.assertIn(str(project_canonical), project_result.stdout)
        self.assertTrue((project_canonical / "scripts" / "adhd_md.py").is_file())
        for rel in (
            ".claude/skills/adhd-md",
            ".codex/skills/adhd-md",
            ".grok/skills/adhd-md",
            ".cursor/skills/adhd-md",
        ):
            installed = self.project / rel
            self.assertTrue(installed.is_dir(), rel)
            self.assertFalse(installed.is_symlink(), rel)
            self.assertEqual((installed / ".adhd-md-managed").read_text(encoding="utf-8"), OWNER_TOKEN + "\n")

        project_uninstall = self.run_uninstall("--project")
        self.assertEqual(project_uninstall.returncode, 0, project_uninstall.stderr)
        self.assertFalse(project_canonical.exists())
        self.assertTrue(canonical.is_dir(), "project uninstall must keep user canonical")
        self.assertTrue(prompt.is_file(), "project uninstall must keep user-level prompt")


if __name__ == "__main__":
    unittest.main()
