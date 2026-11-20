#!/bin/sh
set -eu

# Use the same immutable Bubblewrap source as the native SDK sandbox jobs.
source_commit=2a76602a8c71f36c1527cf9fc3417d9149822e0c
apt-get update
apt-get install -y --no-install-recommends ca-certificates gcc git libc6-dev libcap-dev meson ninja-build pkg-config
git init /tmp/bubblewrap
git -C /tmp/bubblewrap fetch --depth=1 https://github.com/containers/bubblewrap.git "$source_commit"
git -C /tmp/bubblewrap checkout --detach FETCH_HEAD
test "$(git -C /tmp/bubblewrap rev-parse HEAD)" = "$source_commit"
meson setup /tmp/bubblewrap/build /tmp/bubblewrap --prefix=/usr -Dman=disabled -Dtests=false
meson compile -C /tmp/bubblewrap/build
DESTDIR=/out meson install -C /tmp/bubblewrap/build --no-rebuild
test -x /out/usr/bin/bwrap
test ! -u /out/usr/bin/bwrap

