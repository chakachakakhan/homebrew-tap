cask "chatgpt-linux" do
  arch arm: "arm64", intel: "amd64"

  version "26.1007.71326"
  sha256 arm64_linux:  "d9fbd854a1522edb2b53c755a3ea5ecfa67b3f8c035313405b50967242efba0a",
         x86_64_linux: "0e006b4931712f5a90d4cd04972c6e0b533cedcdfdb2b51946d5b9367471f556"

  url "https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_#{version}_#{arch}.deb"
  name "ChatGPT"
  desc "OpenAI's official desktop app with ChatGPT and Codex"
  homepage "https://learn.chatgpt.com/docs/linux/linux-app"

  livecheck do
    url "https://persistent.oaistatic.com/codex-app-prod/linux/deb/dists/stable/main/binary-#{arch}/Packages"
    regex(/^Version:\s*(\d+(?:\.\d+)+)$/i)
  end

  depends_on formula: "dpkg"
  depends_on linux: :any

  binary "usr/lib/chatgpt/codex-launcher", target: "chatgpt"
  artifact "usr/share/applications/chatgpt.desktop",
           target: "#{Dir.home}/.local/share/applications/chatgpt.desktop"
  artifact "usr/share/pixmaps/chatgpt.png",
           target: "#{Dir.home}/.local/share/icons/chatgpt.png"
  artifact "usr/share/metainfo/com.openai.chatgpt.metainfo.xml",
           target: "#{Dir.home}/.local/share/metainfo/com.openai.chatgpt.metainfo.xml"

  preflight_steps do
    # Extract only the .deb data archive. Do not run distro maintainer scripts
    # or write package-managed files into privileged system directories.
    remove ["usr", "etc"], recursive: true
    run "{{HOMEBREW_PREFIX}}/opt/dpkg/bin/dpkg-deb",
        args: ["-x", "{{staged_path}}/chatgpt_{{version}}_{{arch}}.deb", "{{staged_path}}"]
    remove "chatgpt_{{version}}_{{arch}}.deb"

    inreplace "usr/share/applications/chatgpt.desktop", /^Exec=.*/,
              "Exec={{HOMEBREW_PREFIX}}/bin/chatgpt %U", audit_result: false
    inreplace "usr/share/applications/chatgpt.desktop", /^Icon=.*/, "Icon=chatgpt", audit_result: false
  end

  zap trash: [
    "~/.cache/ChatGPT",
    "~/.cache/Codex",
    "~/.config/ChatGPT",
    "~/.config/Codex",
    "~/.local/share/ChatGPT",
    "~/.local/share/Codex",
  ]
end
