class EmacsPgtk < Formula
  desc "GNU Emacs with native Wayland, native compilation, and tree-sitter"
  homepage "https://www.gnu.org/software/emacs/"
  url "https://ftpmirror.gnu.org/emacs/emacs-31.1.tar.xz"
  mirror "https://ftp.gnu.org/gnu/emacs/emacs-31.1.tar.xz"
  sha256 "1da5790d9580c81932b5bf700633114468da7b3412d69faa767daebf974f4586"
  license "GPL-3.0-or-later"

  livecheck do
    # GNU's mirror selector can redirect the index to HTTP; check GNU over HTTPS.
    url "https://ftp.gnu.org/gnu/emacs/" # rubocop:disable FormulaAudit/Urls
    regex(/href=["']?emacs[._-]v?(\d+\.[1-9]\d*(?:\.\d+)?)\.t/i)
    strategy :page_match
  end

  depends_on "pkgconf" => :build
  depends_on "texinfo" => :build
  depends_on "cairo"
  depends_on "dbus"
  depends_on "gcc"
  depends_on "giflib"
  depends_on "gmp"
  depends_on "gnutls"
  depends_on "gtk+3"
  depends_on "harfbuzz"
  depends_on "jpeg-turbo"
  depends_on "libgccjit"
  depends_on "libpng"
  depends_on "librsvg"
  depends_on "libtiff"
  depends_on "libxml2"
  depends_on :linux
  depends_on "little-cms2"
  depends_on "ncurses"
  depends_on "sqlite"
  depends_on "tree-sitter"
  depends_on "webp"
  depends_on "zlib-ng-compat"

  conflicts_with "emacs", because: "both install emacs, emacsclient, and etags"

  def install
    # libgccjit uses GCC's version-independent Homebrew library directory.
    jit_lib = formula_opt_lib("libgccjit")/"gcc/current"
    ENV.append "LDFLAGS", "-L#{jit_lib} -Wl,-rpath,#{jit_lib}"

    args = %W[
      --prefix=#{prefix}
      --infodir=#{info}/emacs
      --enable-locallisppath=#{HOMEBREW_PREFIX}/share/emacs/site-lisp
      --disable-silent-rules
      --disable-acl
      --with-pgtk
      --with-native-compilation=aot
      --with-tree-sitter
      --with-modules
      --with-gnutls
      --with-dbus
      --with-xml2
      --with-sqlite3
      --without-ns
      --without-imagemagick
      --without-selinux
      --without-sound
      --without-pop
    ]

    # Keep Homebrew's temporary compiler shims out of the dumped exec-path.
    (buildpath/"lisp/site-load.el").write <<~LISP
      (setq exec-path (delete nil
        (mapcar (lambda (path)
                  (unless (string-match-p "Homebrew/shims" path) path))
                exec-path)))
    LISP

    system "./configure", *args
    system "make"
    system "make", "install"
  end

  service do
    run [opt_bin/"emacs", "--fg-daemon"]
    keep_alive true
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/emacs --version")
    assert_equal "42", shell_output("#{bin}/emacs -Q --batch --eval '(princ (+ 20 22))'")
    features = shell_output("#{bin}/emacs -Q --batch --eval '(princ system-configuration-features)'")
    %w[PGTK NATIVE_COMP TREE_SITTER GNUTLS LIBXML2 MODULES SQLITE3].each do |feature|
      assert_match feature, features
    end

    # Loading comp alone misses broken compiler/linker lookup after bottling.
    (testpath/"native-test.el").write "(defun tap-native-test () (+ 20 22))\n"
    (testpath/"check.el").write <<~LISP
      (require 'comp)
      (unless (native-comp-available-p) (error "Native compilation unavailable"))
      (load (native-compile "native-test.el") nil nil t)
      (unless (native-comp-function-p (symbol-function 'tap-native-test))
        (error "Function was not natively compiled"))
      (princ (tap-native-test))
    LISP
    assert_equal "42", shell_output("#{bin}/emacs -Q --batch -l check.el").strip
  end
end
