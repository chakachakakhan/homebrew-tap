class Opencodex < Formula
  desc "Provider proxy for Codex, Claude Code, and other coding clients"
  homepage "https://github.com/lidge-jun/opencodex"
  version "2.99.0"
  license "MIT"

  if Hardware::CPU.arm?
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-arm64.tar.gz"
    sha256 "e7ad7fea05d5c91c8a53d1c44190f97bbb5c5bb2797b0e9e52e5aff4df734929"
  else
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-x64.tar.gz"
    sha256 "d3456c5b5fcf263bb07adc23612bccf1539ebd62c2d803d347aed735b860dd02"
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
