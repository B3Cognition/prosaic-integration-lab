"""Conservative consumer plan admission, not OS enforcement or authorization."""
import math
import os
from pathlib import Path
import stat

from prosaic_runtime import RuntimeConfig,RunPolicy

CONTROLS=('filesystem','network','credentials','timeout','output','same_group_cleanup')
UNSUPPORTED=('cpu','memory','process_count','detached_cleanup')


def admit_sandbox(config, policy, *, workspace, manifest, required_controls):
    """Inspect trusted host inputs only; no probes, model requests or fallback.

    A ready plan still needs host approval and successful public SDK preflight.
    Runtime's implicit interpreter/libraries are trusted dependencies. Explicit
    extra runtime roots and environment passing are outside this narrow recipe.
    """
    if (type(required_controls) not in (tuple,list) or not 1<=len(required_controls)<=10
        or any(type(c) is not str or c not in CONTROLS+UNSUPPORTED for c in required_controls)
        or len(set(required_controls))!=len(required_controls)):
        raise ValueError('explicit known unique controls required')
    def result(reason,unsupported=()):
        return dict(version=1,admitted=reason=='ready',reason=reason,unsupportedControls=list(unsupported))
    unsupported=sorted(set(required_controls)&set(UNSUPPORTED))
    if unsupported:return result('unsupported_controls',unsupported)
    if type(config) is not RuntimeConfig or type(policy) is not RunPolicy or type(manifest) is not dict:
        raise ValueError('trusted SDK configuration and manifest required')
    if config.cli_sandbox.mode!='required':return result('sandbox_required')
    if config.cli_sandbox.runtime_roots:return result('extra_runtime_roots')
    if manifest.get('pass_env',[])!=[]:return result('environment_grant')
    timeout=manifest.get('timeout_s');maximum=manifest.get('max_output_bytes')
    if (type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30
        or type(maximum) is not int or not 128<=maximum<=8192):
        return result('manifest_bounds')
    name=manifest.get('name')
    if (type(name) is not str or config.allowed_tools!=frozenset({name})
        or policy.allowed_tools!=frozenset({name})):
        return result('tool_grant')
    for value,limit in ((policy.max_provider_requests,4),(policy.max_tool_calls,2),(policy.max_reported_tokens,8192)):
        if type(value) is not int or not 1<=value<=limit:return result('invocation_bounds')
    if policy.timeout_s>600 or any(ep.max_tokens is None or ep.max_tokens>512 for ep in config.profiles.values()):
        return result('invocation_bounds')
    root=Path(workspace)
    try:
        if (not root.is_absolute() or any(p.is_symlink() for p in (root,*root.parents))
            or root.resolve() in (Path('/'),Path.home().resolve())):
            return result('workspace')
        info=root.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode & 0o077:
            return result('workspace')
        if not policy.read_roots:return result('evidence_grant')
        for relative in (*policy.read_roots,*policy.forbidden_roots):
            path=Path(relative)
            resolved=(root/path).resolve()
            if (path.is_absolute() or '..' in path.parts or resolved==root
                or not resolved.is_relative_to(root) or not resolved.exists()):
                return result('evidence_grant')
        visited=0
        for relative in policy.read_roots:
            path=root/relative
            candidates=[path]
            if path.is_dir():
                for base,directories,files in os.walk(path,followlinks=False):
                    candidates.extend(Path(base)/name for name in directories+files)
                    if len(candidates)>256:return result('evidence_grant')
            for entry in candidates:
                visited+=1
                if visited>256:return result('evidence_grant')
                if stat.S_ISSOCK(entry.stat().st_mode):return result('socket_grant')
                if entry.is_symlink() and entry.is_dir():return result('evidence_grant')
    except (OSError,ValueError,RuntimeError):
        return result('evidence_grant')
    return result('ready')
