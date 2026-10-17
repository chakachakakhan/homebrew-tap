class Opencodex < Formula
  desc "Provider proxy for Codex, Claude Code, and other coding clients"
  homepage "https://github.com/lidge-jun/opencodex"
  version "2.88.0"
  license "MIT"

  if Hardware::CPU.arm?
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-arm64.tar.gz"
    sha256 "bd8842c615a09dccb3d92e70ddb047288bcb972996a731c7e5cc1178b79ff256"
  else
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-x64.tar.gz"
    sha256 "965432b74ff34aff88cdaea384c5b44b547d2dc48bc13cac3ac58a4e496aaa10"
  end

  depends_on :linux

  def install
    # The compiled runtime resolves dashboard and native addons beside its real executable.
    libexec.install "ocx", "gui", "keyring"
    bin.install_symlink libexec/"ocx"
    bin.install_symlink libexec/"ocx" => "opencodex"
  end

  def caveats
    <<~EOS
      Run ocx start to start the proxy, or ocx service to install its background service.
      Open the dashboard at http://localhost:10100.
      Update this installation with brew upgrade --formula chakachakakhan/tap/opencodex.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/ocx --version")
    assert_match version.to_s, shell_output("#{bin}/opencodex --version")
  end
end
