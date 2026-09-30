cask "thorium-reader-linux" do
  arch arm: "arm64", intel: "x86_64"

  version "3.5.1"
  sha256 arm64_linux:  "4bd7c79973a819d107fa5a7084585c7343efa4614bf2585dc8b2945f03eaadb1",
         x86_64_linux: "906675d518197a4e88eff1d349818db21e49c7979806c325b52e30e31dd22312"

  url "https://github.com/edrlab/thorium-reader/releases/download/v#{version}/Thorium-#{version}-#{arch}.AppImage"
  name "Thorium Reader"
  desc "Accessible ebook reader supporting EPUB, PDF, audiobooks, and Readium LCP"
  homepage "https://thorium.edrlab.org/"

  livecheck do
    url :url
    regex(/^v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end

  depends_on linux: :any

  binary "squashfs-root/AppRun", target: "thorium-reader"
  artifact "squashfs-root/thorium.desktop",
           target: "#{Dir.home}/.local/share/applications/thorium-reader.desktop"
  artifact "squashfs-root/usr/share/icons/hicolor/1024x1024/apps/thorium.png",
           target: "#{Dir.home}/.local/share/icons/thorium-reader.png"

  preflight_steps do
    # The upstream AppImage can extract itself without FUSE or distro installation.
    remove "squashfs-root", recursive: true
    set_permissions "Thorium-{{version}}-{{arch}}.AppImage", "+x", recursive: false
    run "Thorium-{{version}}-{{arch}}.AppImage", args: ["--appimage-extract"],
                                             base: :staged_path, chdir: "{{staged_path}}"
    remove "Thorium-{{version}}-{{arch}}.AppImage"

    # AppRun retains upstream's conditional Electron sandbox handling.
    inreplace "squashfs-root/thorium.desktop", /^Exec=.*/,
              "Exec={{HOMEBREW_PREFIX}}/bin/thorium-reader %U", audit_result: false
    inreplace "squashfs-root/thorium.desktop", /^Icon=.*/, "Icon=thorium-reader", audit_result: false
  end

  zap trash: "~/.config/EDRLab.ThoriumReader"
end
