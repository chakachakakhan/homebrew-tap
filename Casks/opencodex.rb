cask "opencodex" do
  version "2.76.0"
  sha256 arm:          "bfe77313bd9b26c4e484b09c5bdad1b4626d945554980aa2ec285cd2794e6b79",
         intel:        "bfe77313bd9b26c4e484b09c5bdad1b4626d945554980aa2ec285cd2794e6b79",
         x86_64_linux: "da5e60b4d9a9f68a2af70c814c130a0eadfe58dab5f40c81454695f1b1d6246c"

  on_macos do
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/OpenCodex-#{version}-macos.dmg"

    auto_updates true
    depends_on macos: :ventura

    app "OpenCodex.app"

    uninstall quit: "com.opencodex.desktop"

    zap trash: [
      "~/.opencodex",
      "~/Library/Application Support/com.opencodex.desktop",
      "~/Library/Caches/com.opencodex.desktop",
      "~/Library/Preferences/com.opencodex.desktop.plist",
    ]
  end
  on_linux do
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/OpenCodex-#{version}-linux-x86_64.AppImage"

    depends_on arch: :x86_64

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

  name "OpenCodex"
  desc "Desktop provider proxy and dashboard for coding clients"
  homepage "https://github.com/lidge-jun/opencodex"

  livecheck do
    url :url
    regex(/^v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end
end
