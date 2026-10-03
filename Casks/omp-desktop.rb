cask "omp-desktop" do
  version "0.5.0"
  sha256 "0072a652e09be57113e940ddd6c728bf45db72acfe6174f68a14a801bc277eb4"

  url "https://github.com/apoc/omp-desktop/releases/download/v#{version}/OMP.Desktop_#{version}_amd64.AppImage"
  name "OMP Desktop"
  desc "Desktop workspace for Oh My Pi with chat, plans, diffs, and subagents"
  homepage "https://github.com/apoc/omp-desktop"

  livecheck do
    url :url
    regex(/^v?(\d+(?:\.\d+)+)$/i)
    strategy :github_latest
  end

  depends_on arch: :x86_64, linux: :any

  binary "omp-desktop-launcher", target: "omp-desktop"
  artifact "omp-desktop.desktop",
           target: "#{Dir.home}/.local/share/applications/omp-desktop.desktop"
  artifact "omp-desktop.png",
           target: "#{Dir.home}/.local/share/icons/omp-desktop.png"

  preflight_steps do
    # Preserve the upstream GTK setup and bundled libraries without requiring FUSE.
    remove "squashfs-root", recursive: true
    set_permissions "OMP.Desktop_{{version}}_amd64.AppImage", "+x", recursive: false
    run "OMP.Desktop_{{version}}_amd64.AppImage", args: ["--appimage-extract"],
                                               base: :staged_path, chdir: "{{staged_path}}"
    remove "OMP.Desktop_{{version}}_amd64.AppImage"

    # Keep AppRun's GTK/WebKit paths and working directory, but stop its generic
    # shim from redirecting external Python tools to an absent bundled runtime.
    # Fixed-width private environment keys leave ELF offsets unchanged.
    inreplace "squashfs-root/AppRun.wrapped", "PYTHONHOME", "APP_PYHOME"
    inreplace "squashfs-root/AppRun.wrapped", "PYTHONPATH", "APP_PYPATH"

    # Tauri's fixed-width bundle marker controls whether its updater replaces
    # this executable. An extracted Homebrew installation must be notify-only.
    # A changed upstream marker aborts installation for a reviewed adjustment.
    inreplace "squashfs-root/usr/bin/omp-desktop",
              "__TAURI_BUNDLE_TYPE_VAR_APP", "__TAURI_BUNDLE_TYPE_VAR_UNK"

    write_file "omp-desktop-launcher", <<~SH
      #!/bin/bash
      export PATH="{{HOMEBREW_PREFIX}}/bin:{{HOMEBREW_PREFIX}}/sbin:${PATH:-/usr/bin:/bin}"
      # AppRun changes directory for WebKit; resolve project folders first.
      args=()
      for argument in "$@"; do
        if [[ -d "$argument" ]]; then
          argument="$(readlink -f -- "$argument")"
        fi
        args+=("$argument")
      done
      exec "{{staged_path}}/squashfs-root/AppRun" "${args[@]}"
    SH
    set_permissions "omp-desktop-launcher", "+x", recursive: false

    write_file "omp-desktop.desktop", <<~DESKTOP
      [Desktop Entry]
      Name=OMP Desktop
      Comment=Desktop workspace for Oh My Pi
      Exec={{HOMEBREW_PREFIX}}/bin/omp-desktop %F
      Icon=omp-desktop
      Terminal=false
      Type=Application
      Categories=Development;
      MimeType=inode/directory;
      StartupWMClass=omp-desktop
    DESKTOP
    copy "squashfs-root/usr/share/icons/hicolor/128x128/apps/omp-desktop.png", "omp-desktop.png"
  end

  zap trash: [
    "~/.cache/dev.ohMyPi.desktop",
    "~/.config/dev.ohMyPi.desktop",
    "~/.local/share/dev.ohMyPi.desktop",
  ]

  caveats do
    <<~EOS
      Uses your existing Oh My Pi (omp) installation and sessions.
      If needed, install the engine with brew install can1357/tap/omp.
      Launch from your application menu or run omp-desktop /path/to/project.
      Update this installation with brew upgrade --cask chakachakakhan/tap/omp-desktop.
    EOS
  end
end
