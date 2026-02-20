import os
import re
import shutil
import stat
import time
import zipfile
from pathlib import Path

from cgpt.core.constants import MAX_ZIP_MEMBERS, MAX_ZIP_UNCOMPRESSED_BYTES
from cgpt.core.layout import die


def is_unsafe_zip_member(member_name: str, dest_dir: Path) -> bool:
    """Return True when a ZIP member path is unsafe for extraction."""
    normalized = member_name.replace("\\", "/")
    if not normalized or normalized == ".":
        return True
    if normalized == ".." or normalized.startswith(("/", "../")):
        return True
    if "/../" in normalized:
        return True
    if re.match(r"^[a-zA-Z]:", member_name) or re.match(r"^[a-zA-Z]:", normalized):
        return True

    dest_root = dest_dir.resolve()
    candidate = (dest_dir / normalized).resolve()
    try:
        candidate.relative_to(dest_root)
    except ValueError:
        return True
    return False

def is_special_zip_member(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    if not mode:
        return False
    file_type = stat.S_IFMT(mode)
    if not file_type:
        return False
    return file_type not in (stat.S_IFREG, stat.S_IFDIR)

def validate_zip_members_safe(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    member_count = 0
    total_uncompressed = 0
    for info in zf.infolist():
        member_count += 1
        if member_count > MAX_ZIP_MEMBERS:
            die(
                f"ZIP member limit exceeded: {member_count} > {MAX_ZIP_MEMBERS} members."
            )
        if is_special_zip_member(info):
            die(f"Special ZIP member type is not allowed: {info.filename}")
        if is_unsafe_zip_member(info.filename, dest_dir):
            die(f"Unsafe ZIP member path detected: {info.filename}")
        if info.is_dir():
            continue
        total_uncompressed += max(int(info.file_size), 0)
        if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
            die(
                "ZIP uncompressed size limit exceeded: "
                f"{total_uncompressed} > {MAX_ZIP_UNCOMPRESSED_BYTES} bytes."
            )

def extract_zip_safely(zpath: Path, out_dir: Path) -> None:
    parent = out_dir.parent
    temp_dir = parent / f".{out_dir.name}.tmp-{os.getpid()}-{int(time.time() * 1_000_000)}"
    try:
        with zipfile.ZipFile(zpath, "r") as zf:
            validate_zip_members_safe(zf, out_dir)
            temp_dir.mkdir(parents=True, exist_ok=False)
            zf.extractall(temp_dir)

        if out_dir.exists():
            if out_dir.is_symlink() or not out_dir.is_dir():
                die(f"Refusing to replace non-directory extraction target: {out_dir}")
            shutil.rmtree(out_dir)

        temp_dir.replace(out_dir)
    except zipfile.BadZipFile as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        die(f"Invalid ZIP file: {zpath}\n{e}")
    except BaseException:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
