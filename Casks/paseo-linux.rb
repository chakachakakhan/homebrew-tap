cask "paseo-linux" do
  version "0.13.0"
  sha256 "1cc150fece4e9ed56564a75a0894e5460a2033203cc6b1bd8a78375e9bab447a"

  url "https://github.com/getpaseo/paseo/releases/download/v#{version}/Paseo-#{version}-x64.tar.gz"
  name "Paseo"
  desc "Desktop app and CLI for managing AI coding agents"
  homepage "https://github.com/getpaseo/paseo"

  livecheck do
    url :url
    regex(/^v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end

  conflicts_with cask: "paseo"
  depends_on arch: :x86_64, linux: :any

  binary "Paseo-#{version}-x64/Paseo", target: "paseo-desktop"
  binary "Paseo-#{version}-x64/resources/bin/paseo"
  artifact "paseo.desktop",
           target: "#{Dir.home}/.local/share/applications/paseo.desktop"
  artifact "paseo.png",
           target: "#{Dir.home}/.local/share/icons/paseo.png"

  preflight_steps do
    # Preserve Paseo's upstream Electron sandbox logic and register paseo:// URLs.
    copy "Paseo-{{version}}-x64/resources/icon.png", "paseo.png"
    write_file "paseo.desktop", <<~DESKTOP
      [Desktop Entry]
      Name=Paseo
      Comment=Manage AI coding agents
      Exec={{HOMEBREW_PREFIX}}/bin/paseo-desktop %U
      Icon=paseo
      Terminal=false
      Type=Application
      Categories=Development;
      MimeType=x-scheme-handler/paseo;
    DESKTOP
  end

  postflight_steps do
    symlink ".local/share/applications", "user-applications",
            source_base: :home, overwrite: true
    run "/usr/bin/update-desktop-database",
        args: ["{{staged_path}}/user-applications"],
        writable_paths: [".local/share/applications"], writable_base: :home, must_succeed: false
  end

  uninstall_postflight_steps do
    symlink ".local/share/applications", "user-applications",
            source_base: :home, overwrite: true
    run "/usr/bin/update-desktop-database",
        args: ["{{staged_path}}/user-applications"],
        writable_paths: [".local/share/applications"], writable_base: :home, must_succeed: false
  end

  caveats do
    <<~EOS
      Launch Paseo from your application menu or run paseo-desktop.
      Run the CLI with paseo. Updates are provided by Homebrew:
        brew upgrade --cask chakachakakhan/tap/paseo-linux
      Uninstalling this cask keeps your ~/.paseo agents, worktrees, and configuration.
    EOS
  end
end
