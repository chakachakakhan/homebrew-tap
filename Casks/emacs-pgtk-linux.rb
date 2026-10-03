cask "emacs-pgtk-linux" do
  version "31.1"
  sha256 "1da5790d9580c81932b5bf700633114468da7b3412d69faa767daebf974f4586"

  # Only desktop entries and the icon are taken from this source archive.
  # The formula supplies Emacs itself as a standard Homebrew bottle.
  url "https://ftpmirror.gnu.org/emacs/emacs-#{version}.tar.xz"
  name "GNU Emacs"
  desc "Desktop integration for the native Wayland build of GNU Emacs"
  homepage "https://www.gnu.org/software/emacs/"

  livecheck do
    url "https://ftp.gnu.org/gnu/emacs/"
    regex(/href=["']?emacs[._-]v?(\d+\.[1-9]\d*(?:\.\d+)?)\.t/i)
    strategy :page_match
  end

  depends_on formula: "chakachakakhan/tap/emacs-pgtk"
  depends_on linux: :any

  artifact "emacs-#{version}/etc/emacs.desktop",
           target: "#{Dir.home}/.local/share/applications/emacs.desktop"
  artifact "emacs-#{version}/etc/emacsclient.desktop",
           target: "#{Dir.home}/.local/share/applications/emacsclient.desktop"
  artifact "emacs-#{version}/etc/images/icons/hicolor/scalable/apps/emacs.svg",
           target: "#{Dir.home}/.local/share/icons/emacs.svg"

  preflight_steps do
    inreplace "emacs-{{version}}/etc/emacs.desktop", "Exec=emacs %F",
              "Exec={{HOMEBREW_PREFIX}}/opt/emacs-pgtk/bin/emacs %F"
    inreplace "emacs-{{version}}/etc/emacsclient.desktop", "emacsclient --",
              "{{HOMEBREW_PREFIX}}/opt/emacs-pgtk/bin/emacsclient --"
    inreplace "emacs-{{version}}/etc/emacsclient.desktop", "Exec=emacs %F",
              "Exec={{HOMEBREW_PREFIX}}/opt/emacs-pgtk/bin/emacs %F"
  end

  caveats <<~EOS
    Emacs, emacsclient, and the daemon are supplied by the emacs-pgtk formula.
    To start the daemon at login:
      brew services start chakachakakhan/tap/emacs-pgtk
    Upgrade both the formula and this desktop integration with brew upgrade.
    Uninstalling this cask removes the desktop entries and icon; uninstall the
    formula separately to remove Emacs itself. Emacs and Doom settings are preserved.
  EOS
end
