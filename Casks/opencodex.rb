cask "opencodex" do
  version "2.80.0"
  sha256 "0805350a60849b5d02c30b4f74a6bb6b51407b06ce72c5cab3f8e13c4cf46654"

  url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/OpenCodex-#{version}-linux-x86_64.AppImage"
  name "OpenCodex"
  desc "Desktop provider proxy and dashboard for coding clients"
  homepage "https://github.com/lidge-jun/opencodex"

  livecheck do
    url :url
    regex(/^v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end

  depends_on arch: :x86_64, linux: :any

  binary "squashfs-root/AppRun", target: "opencodex-desktop"
  artifact "opencodex-desktop.desktop",
           target: "#{Dir.home}/.local/share/applications/opencodex-desktop.desktop"
  artifact "opencodex-desktop.png",
           target: "#{Dir.home}/.local/share/icons/opencodex-desktop.png"

  preflight_steps do
    # Keep the upstream AppRun, libraries, sidecar, and dashboard together without FUSE.
    remove "squashfs-root", recursive: true
    set_permissions "OpenCodex-{{version}}-linux-x86_64.AppImage", "+x", recursive: false
    run "OpenCodex-{{version}}-linux-x86_64.AppImage", args: ["--appimage-extract"],
                                                 base: :staged_path, chdir: "{{staged_path}}"
    remove "OpenCodex-{{version}}-linux-x86_64.AppImage"
    # Resolve the script before its parent directory when launched through Homebrew's symlink.
    inreplace "squashfs-root/AppRun",
              'this_dir="$(readlink -f "$(dirname "$0")")"',
              'this_dir="$(dirname "$(readlink -f "$0")")"'
    # Preserve the original desktop file inside the AppDir for AppRun's own lookup.
    copy "squashfs-root/OpenCodex.desktop", "opencodex-desktop.desktop"
    copy "squashfs-root/usr/share/icons/hicolor/512x512/apps/opencodex-desktop.png", "opencodex-desktop.png"
    inreplace "opencodex-desktop.desktop", /^Exec=.*/,
              "Exec={{HOMEBREW_PREFIX}}/bin/opencodex-desktop", audit_result: false
  end

  zap trash: [
    "~/.cache/com.opencodex.desktop",
    "~/.config/com.opencodex.desktop",
    "~/.local/share/com.opencodex.desktop",
    "~/.opencodex",
  ]

  caveats do
    <<~EOS
      Launch OpenCodex from your application menu or run opencodex-desktop.
      Update this extracted installation with:
        brew upgrade --cask chakachakakhan/tap/opencodex
    EOS
  end
end
